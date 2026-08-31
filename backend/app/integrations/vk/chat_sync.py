import logging

from app.core.config import get_settings
from app.integrations.vk.client import ChatReference, VkApiError, VkClient, build_client
from app.services.chat_directory import sync_chat

logger = logging.getLogger(__name__)


async def sync_chat_reference(client: VkClient, reference: ChatReference) -> None:
    if reference.title is None:
        try:
            reference = await client.get_chat(reference.peer_id)
        except VkApiError:
            logger.exception("Failed to load VK chat %s title", reference.peer_id)
    members = await client.get_members(reference.peer_id)
    await sync_chat(reference.peer_id, members, title=reference.title)
    logger.info("VK chat %s synchronized with %s users", reference.peer_id, len(members))


async def sync_available_chats() -> int:
    """Discover every available VK chat and persist its current members."""
    client = build_client(get_settings())
    chats = await client.list_chats()
    for chat in chats:
        await sync_chat_reference(client, chat)
    return len(chats)
