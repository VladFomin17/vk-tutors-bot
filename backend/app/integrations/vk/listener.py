import asyncio
import logging
from datetime import UTC, datetime
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
from app.integrations.vk.confirmations import parse_confirmation, parse_outbound_message
from app.integrations.vk.media import store_images
from app.services.chat_directory import (
    list_chats_missing_titles,
    mark_chat_activity,
    needs_sync,
    sync_chat,
)
from app.services.media import MediaJob, list_missing_media_jobs, remove_files, replace_response_media
from app.services.outbox import remember_delivery
from app.services.responses import record_confirmation

logger = logging.getLogger(__name__)


def parse_chat_message(update: dict[str, Any]) -> tuple[int, int, datetime] | None:
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
    timestamp = message.get("date")
    if not isinstance(peer_id, int) or peer_id < 2_000_000_000:
        return None
    if not isinstance(from_id, int) or not isinstance(timestamp, int) or timestamp <= 0:
        return None
    try:
        occurred_at = datetime.fromtimestamp(timestamp, UTC)
    except (OverflowError, OSError, ValueError):
        return None
    return peer_id, from_id, occurred_at


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
    outbound_message = parse_outbound_message(update, client.group_id)
    if outbound_message is not None:
        await remember_delivery(**vars(outbound_message))
        return

    message = parse_chat_message(update)
    if message is not None:
        peer_id, from_id, occurred_at = message
        if await needs_sync(peer_id, from_id):
            await sync_reference(client, ChatReference(peer_id, None))
        await mark_chat_activity(peer_id, occurred_at)
    confirmation = parse_confirmation(update, client.group_id)
    if confirmation is not None:
        if message is None:
            await mark_chat_activity(confirmation.peer_id, confirmation.responded_at)
        result = await record_confirmation(**vars(confirmation))
        settings = get_settings()
        remove_files(settings.media_root, list(result.obsolete_storage_names))
        if result.media_job is not None:
            await store_media(result.media_job)
        if result.status != "ignored":
            logger.info(
                "VK confirmation from user %s: %s",
                confirmation.vk_user_id,
                result.status,
            )


async def store_media(job: MediaJob) -> None:
    settings = get_settings()
    files = await store_images(
        job,
        settings.media_root,
        settings.max_attachment_bytes,
        settings.vk_request_timeout_seconds,
    )
    old_names = await replace_response_media(job, files)
    new_names = {file.storage_name for file in files}
    if old_names is None:
        remove_files(settings.media_root, list(new_names))
        return
    remove_files(
        settings.media_root,
        [storage_name for storage_name in old_names if storage_name not in new_names],
    )
    if files:
        logger.info("Stored %s image(s) for response %s", len(files), job.response_id)


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
        for job in await list_missing_media_jobs():
            try:
                await store_media(job)
            except OSError:
                logger.exception("Failed to restore media for response %s", job.response_id)

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
