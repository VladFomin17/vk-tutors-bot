import asyncio
import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import engine
from app.integrations.vk.client import (
    ChatReference,
    LongPollEndpoint,
    VkApiError,
    VkClient,
    build_client,
)
from app.integrations.vk.confirmations import parse_confirmation
from app.services.chat_directory import list_chats_missing_titles, needs_sync, sync_chat
from app.services.responses import record_confirmation

logger = logging.getLogger(__name__)


def parse_chat_message(update: dict[str, Any]) -> tuple[int, int] | None:
    if update.get("type") != "message_new":
        return None
    event_object = update.get("object")
    if not isinstance(event_object, dict):
        return None
    message = event_object.get("message")
    if not isinstance(message, dict):
        return None
    peer_id = message.get("peer_id")
    from_id = message.get("from_id")
    if not isinstance(peer_id, int) or peer_id < 2_000_000_000:
        return None
    if not isinstance(from_id, int):
        return None
    return peer_id, from_id


async def sync_reference(client: VkClient, reference: ChatReference) -> None:
    if reference.title is None:
        try:
            reference = await client.get_chat(reference.peer_id)
        except VkApiError:
            logger.exception("Failed to load VK chat %s title", reference.peer_id)
    members = await client.get_members(reference.peer_id)
    await sync_chat(reference.peer_id, members, title=reference.title)
    logger.info("VK chat %s synchronized with %s users", reference.peer_id, len(members))


async def handle_update(client: VkClient, update: dict[str, Any]) -> None:
    message = parse_chat_message(update)
    if message is None:
        return
    peer_id, from_id = message
    if await needs_sync(peer_id, from_id):
        await sync_reference(client, ChatReference(peer_id, None))
    confirmation = parse_confirmation(update, client.group_id)
    if confirmation is not None:
        result = await record_confirmation(**vars(confirmation))
        if result != "ignored":
            logger.info("VK confirmation from user %s: %s", confirmation.vk_user_id, result)


async def retry_update(
    client: VkClient,
    update: dict[str, Any],
    max_retries: int,
) -> None:
    for attempt in range(max_retries):
        try:
            await handle_update(client, update)
            return
        except (VkApiError, OSError, SQLAlchemyError):
            if attempt + 1 == max_retries:
                logger.exception("VK update failed after %s attempts", max_retries)
                # ponytail: the next message retries discovery; persist raw events if lossless intake is required.
                return
            await asyncio.sleep(min(2**attempt, 30))


async def run() -> None:
    settings = get_settings()
    client = build_client(settings)

    try:
        try:
            chats = await client.list_chats()
        except VkApiError:
            logger.exception("Failed to load existing VK chats")
            chats = []
        for chat in chats:
            try:
                await sync_reference(client, chat)
            except (VkApiError, SQLAlchemyError):
                logger.exception("Failed to synchronize VK chat %s", chat.peer_id)
        try:
            missing_title_peer_ids = await list_chats_missing_titles()
        except SQLAlchemyError:
            logger.exception("Failed to load VK chats without titles")
            missing_title_peer_ids = []
        for peer_id in missing_title_peer_ids:
            try:
                await sync_reference(client, ChatReference(peer_id, None))
            except (VkApiError, SQLAlchemyError):
                logger.exception("Failed to restore VK chat %s title", peer_id)

        endpoint: LongPollEndpoint | None = None
        while True:
            try:
                if endpoint is None:
                    endpoint = await client.get_long_poll_endpoint()
                    logger.info("VK Long Poll connected")
                result = await client.poll(endpoint)
                if result is None:
                    endpoint = None
                    continue
                ts, updates = result
                for update in updates:
                    await retry_update(client, update, settings.vk_max_retries)
                endpoint = LongPollEndpoint(endpoint.server, endpoint.key, ts)
            except VkApiError:
                logger.exception("VK Long Poll request failed")
                endpoint = None
                await asyncio.sleep(5)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(run())
