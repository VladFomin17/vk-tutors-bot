from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from app.db.session import session_factory
from app.models import ChatMember, StudyGroup, VkChat, VkUser


class DirectoryNotFoundError(RuntimeError):
    pass


class DirectoryConflictError(RuntimeError):
    pass


async def list_study_groups() -> list[dict[str, object]]:
    student_count = (
        select(func.count(ChatMember.vk_user_id))
        .join(VkChat, VkChat.id == ChatMember.chat_id)
        .where(
            VkChat.study_group_id == StudyGroup.id,
            ChatMember.role == "student",
            ChatMember.is_active.is_(True),
        )
        .correlate(StudyGroup)
        .scalar_subquery()
    )
    unknown_count = (
        select(func.count(ChatMember.vk_user_id))
        .join(VkChat, VkChat.id == ChatMember.chat_id)
        .where(
            VkChat.study_group_id == StudyGroup.id,
            ChatMember.role == "unknown",
            ChatMember.is_active.is_(True),
        )
        .correlate(StudyGroup)
        .scalar_subquery()
    )
    last_activity_at = (
        select(func.max(VkChat.last_activity_at))
        .where(VkChat.study_group_id == StudyGroup.id)
        .correlate(StudyGroup)
        .scalar_subquery()
    )
    async with session_factory() as session:
        rows = await session.execute(
            select(
                StudyGroup.id,
                StudyGroup.name,
                StudyGroup.is_active,
                student_count.label("student_count"),
                unknown_count.label("unknown_count"),
                last_activity_at.label("last_activity_at"),
            ).order_by(StudyGroup.name)
        )
        return [dict(row) for row in rows.mappings()]


async def create_study_group(name: str) -> dict[str, object]:
    async with session_factory.begin() as session:
        row = (
            await session.execute(
                insert(StudyGroup)
                .values(name=name)
                .on_conflict_do_nothing(index_elements=[StudyGroup.name])
                .returning(StudyGroup.id, StudyGroup.name, StudyGroup.is_active)
            )
        ).mappings().one_or_none()
        if row is None:
            raise DirectoryConflictError("Study group already exists")
        return dict(row)


async def list_chats() -> list[dict[str, object]]:
    async with session_factory() as session:
        rows = await session.execute(
            select(
                VkChat.id,
                VkChat.peer_id,
                VkChat.title,
                VkChat.study_group_id,
                VkChat.is_active,
            ).order_by(VkChat.id)
        )
        return [dict(row) for row in rows.mappings()]


async def list_chats_missing_titles() -> list[int]:
    async with session_factory() as session:
        rows = await session.scalars(
            select(VkChat.peer_id).where(VkChat.title.is_(None), VkChat.is_active.is_(True))
        )
        return list(rows)


async def mark_chat_activity(peer_id: int, occurred_at: datetime) -> None:
    async with session_factory.begin() as session:
        await session.execute(
            update(VkChat)
            .where(
                VkChat.peer_id == peer_id,
                or_(
                    VkChat.last_activity_at.is_(None),
                    VkChat.last_activity_at < occurred_at,
                ),
            )
            .values(last_activity_at=occurred_at)
        )


async def link_chat(chat_id: int, study_group_id: int | None) -> dict[str, object]:
    try:
        async with session_factory.begin() as session:
            if study_group_id is not None:
                group_exists = await session.scalar(
                    select(StudyGroup.id).where(StudyGroup.id == study_group_id)
                )
                if group_exists is None:
                    raise DirectoryNotFoundError("Study group not found")
            row = (
                await session.execute(
                    update(VkChat)
                    .where(VkChat.id == chat_id)
                    .values(study_group_id=study_group_id)
                    .returning(
                        VkChat.id,
                        VkChat.peer_id,
                        VkChat.title,
                        VkChat.study_group_id,
                        VkChat.is_active,
                    )
                )
            ).mappings().one_or_none()
            if row is None:
                raise DirectoryNotFoundError("VK chat not found")
            return dict(row)
    except IntegrityError as error:
        raise DirectoryConflictError("Study group is already linked") from error


async def list_members(chat_id: int) -> list[dict[str, object]]:
    async with session_factory() as session:
        chat_exists = await session.scalar(select(VkChat.id).where(VkChat.id == chat_id))
        if chat_exists is None:
            raise DirectoryNotFoundError("VK chat not found")
        rows = await session.execute(
            select(
                ChatMember.chat_id,
                ChatMember.vk_user_id,
                VkUser.first_name,
                VkUser.last_name,
                ChatMember.role,
                ChatMember.is_active,
            )
            .join(VkUser, VkUser.vk_user_id == ChatMember.vk_user_id)
            .where(ChatMember.chat_id == chat_id)
            .order_by(VkUser.last_name, VkUser.first_name)
        )
        return [
            {**dict(row), "id": f"{row['chat_id']}:{row['vk_user_id']}"}
            for row in rows.mappings()
        ]


async def update_member_role(chat_id: int, vk_user_id: int, role: str) -> dict[str, object]:
    async with session_factory.begin() as session:
        row = (
            await session.execute(
                update(ChatMember)
                .where(
                    ChatMember.chat_id == chat_id,
                    ChatMember.vk_user_id == vk_user_id,
                )
                .values(role=role)
                .returning(
                    ChatMember.chat_id,
                    ChatMember.vk_user_id,
                    ChatMember.role,
                    ChatMember.is_active,
                )
            )
        ).mappings().one_or_none()
        if row is None:
            raise DirectoryNotFoundError("Chat member not found")
        return {**dict(row), "id": f"{row['chat_id']}:{row['vk_user_id']}"}


async def needs_sync(peer_id: int, vk_user_id: int) -> bool:
    async with session_factory() as session:
        chat = (
            await session.execute(
                select(VkChat.id, VkChat.title).where(VkChat.peer_id == peer_id)
            )
        ).one_or_none()
        if chat is None or chat.title is None:
            return True
        if vk_user_id <= 0:
            return False
        membership = await session.scalar(
            select(ChatMember.vk_user_id).where(
                ChatMember.chat_id == chat.id,
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
