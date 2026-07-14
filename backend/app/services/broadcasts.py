import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.db.session import session_factory
from app.models import (
    Broadcast,
    BroadcastRecipient,
    BroadcastTarget,
    ChatMember,
    OutboundMessage,
    StudyGroup,
    VkChat,
)


class BroadcastConflictError(RuntimeError):
    pass


async def list_broadcasts() -> list[dict[str, object]]:
    target_count = (
        select(func.count(BroadcastTarget.id))
        .where(BroadcastTarget.broadcast_id == Broadcast.id)
        .correlate(Broadcast)
        .scalar_subquery()
    )
    recipient_count = (
        select(func.count(BroadcastRecipient.vk_user_id))
        .join(BroadcastTarget)
        .where(BroadcastTarget.broadcast_id == Broadcast.id)
        .correlate(Broadcast)
        .scalar_subquery()
    )
    async with session_factory() as session:
        rows = await session.execute(
            select(
                Broadcast.id,
                Broadcast.title,
                Broadcast.message_text,
                Broadcast.link,
                Broadcast.deadline,
                Broadcast.confirmation_type,
                Broadcast.created_at,
                target_count.label("target_count"),
                recipient_count.label("recipient_count"),
            ).order_by(Broadcast.created_at.desc())
        )
        return [dict(row) for row in rows.mappings()]


async def create_broadcast(
    *,
    title: str,
    message_text: str,
    link: str | None,
    deadline: datetime,
    confirmation_type: str,
    study_group_ids: list[int],
) -> dict[str, object]:
    now = datetime.now(UTC)
    if deadline <= now:
        raise BroadcastConflictError("Deadline must be in the future")

    async with session_factory.begin() as session:
        destination_rows = (
            await session.execute(
                select(StudyGroup.id, VkChat.id.label("chat_id"))
                .join(VkChat, VkChat.study_group_id == StudyGroup.id)
                .where(
                    StudyGroup.id.in_(study_group_ids),
                    StudyGroup.is_active.is_(True),
                    VkChat.is_active.is_(True),
                )
            )
        ).mappings().all()
        destinations = {row["id"]: row["chat_id"] for row in destination_rows}
        if set(study_group_ids) != set(destinations):
            raise BroadcastConflictError("Every study group must have an active VK chat")

        member_rows = (
            await session.execute(
                select(VkChat.study_group_id, ChatMember.vk_user_id, ChatMember.role)
                .join(ChatMember, ChatMember.chat_id == VkChat.id)
                .where(
                    VkChat.study_group_id.in_(study_group_ids),
                    ChatMember.is_active.is_(True),
                    ChatMember.role.in_(("unknown", "student")),
                )
            )
        ).all()
        if any(row.role == "unknown" for row in member_rows):
            raise BroadcastConflictError("Classify all active chat members before publishing")

        students_by_group = {
            group_id: [row.vk_user_id for row in member_rows if row.study_group_id == group_id]
            for group_id in study_group_ids
        }
        if any(not students for students in students_by_group.values()):
            raise BroadcastConflictError("Every study group must have at least one active student")

        broadcast = Broadcast(
            title=title,
            message_text=message_text,
            link=link,
            deadline=deadline,
            confirmation_type=confirmation_type,
        )
        session.add(broadcast)
        await session.flush()

        reminder_at = deadline - timedelta(hours=24)
        for group_id in study_group_ids:
            target = BroadcastTarget(
                broadcast_id=broadcast.id,
                study_group_id=group_id,
                chat_id=destinations[group_id],
            )
            session.add(target)
            await session.flush()
            session.add_all(
                BroadcastRecipient(target_id=target.id, vk_user_id=vk_user_id)
                for vk_user_id in students_by_group[group_id]
            )
            session.add(_new_outbound_message(target.id, "initial", now))
            if reminder_at > now:
                session.add(_new_outbound_message(target.id, "reminder", reminder_at))

        return {
            "id": broadcast.id,
            "title": broadcast.title,
            "message_text": broadcast.message_text,
            "link": broadcast.link,
            "deadline": broadcast.deadline,
            "confirmation_type": broadcast.confirmation_type,
            "created_at": broadcast.created_at or now,
            "target_count": len(study_group_ids),
            "recipient_count": sum(map(len, students_by_group.values())),
        }


def _new_outbound_message(target_id: int, kind: str, scheduled_at: datetime) -> OutboundMessage:
    return OutboundMessage(
        target_id=target_id,
        kind=kind,
        scheduled_at=scheduled_at,
        random_id=secrets.randbelow(2**31 - 1) + 1,
        broadcast_token=secrets.token_urlsafe(32),
    )
