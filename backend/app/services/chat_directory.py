from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.db.session import session_factory
from app.models import ChatMember, VkChat, VkUser


async def needs_sync(peer_id: int, vk_user_id: int) -> bool:
    async with session_factory() as session:
        chat_id = await session.scalar(select(VkChat.id).where(VkChat.peer_id == peer_id))
        if chat_id is None:
            return True
        if vk_user_id <= 0:
            return False
        membership = await session.scalar(
            select(ChatMember.vk_user_id).where(
                ChatMember.chat_id == chat_id,
                ChatMember.vk_user_id == vk_user_id,
                ChatMember.is_active.is_(True),
            )
        )
        return membership is None


async def sync_chat(
    peer_id: int,
    members: list[tuple[int, str, str]],
    *,
    title: str | None = None,
) -> None:
    async with session_factory.begin() as session:
        chat_values: dict[str, object] = {"peer_id": peer_id, "is_active": True}
        chat_updates: dict[str, object] = {"is_active": True}
        if title is not None:
            chat_values["title"] = title
            chat_updates["title"] = title
        chat_id = await session.scalar(
            insert(VkChat)
            .values(**chat_values)
            .on_conflict_do_update(index_elements=[VkChat.peer_id], set_=chat_updates)
            .returning(VkChat.id)
        )
        if chat_id is None:
            raise RuntimeError("Failed to persist VK chat")

        await session.execute(
            update(ChatMember).where(ChatMember.chat_id == chat_id).values(is_active=False)
        )
        if not members:
            return

        user_rows = [
            {
                "vk_user_id": vk_user_id,
                "first_name": first_name,
                "last_name": last_name,
            }
            for vk_user_id, first_name, last_name in members
        ]
        user_insert = insert(VkUser).values(user_rows)
        await session.execute(
            user_insert.on_conflict_do_update(
                index_elements=[VkUser.vk_user_id],
                set_={
                    "first_name": user_insert.excluded.first_name,
                    "last_name": user_insert.excluded.last_name,
                },
            )
        )

        member_rows = [
            {"chat_id": chat_id, "vk_user_id": vk_user_id}
            for vk_user_id, _, _ in members
        ]
        member_insert = insert(ChatMember).values(member_rows)
        await session.execute(
            member_insert.on_conflict_do_update(
                index_elements=[ChatMember.chat_id, ChatMember.vk_user_id],
                set_={"is_active": True, "last_seen_at": member_insert.excluded.last_seen_at},
            )
        )
