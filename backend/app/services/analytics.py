from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import Date, and_, cast, func, select

from app.db.session import session_factory
from app.models import (
    Broadcast,
    BroadcastRecipient,
    BroadcastResponse,
    BroadcastTarget,
    ChatMember,
    StudyGroup,
    VkChat,
    VkUser,
)

MOSCOW = ZoneInfo("Europe/Moscow")


async def list_students() -> list[dict[str, object]]:
    async with session_factory() as session:
        rows = await session.execute(
            select(
                ChatMember.chat_id,
                ChatMember.vk_user_id,
                VkUser.first_name,
                VkUser.last_name,
                ChatMember.is_active,
                ChatMember.first_seen_at,
                ChatMember.last_seen_at,
                StudyGroup.id.label("study_group_id"),
                StudyGroup.name.label("study_group_name"),
                VkChat.title.label("chat_title"),
            )
            .join(VkUser, VkUser.vk_user_id == ChatMember.vk_user_id)
            .join(VkChat, VkChat.id == ChatMember.chat_id)
            .join(StudyGroup, StudyGroup.id == VkChat.study_group_id)
            .where(ChatMember.role == "student")
            .order_by(StudyGroup.name, VkUser.last_name, VkUser.first_name)
        )
        return [
            {**dict(row), "id": f"{row['chat_id']}:{row['vk_user_id']}"}
            for row in rows.mappings()
        ]


async def get_statistics() -> dict[str, object]:
    now = datetime.now(UTC)
    today = now.astimezone(MOSCOW).date()
    today_start = datetime.combine(today, time.min, MOSCOW).astimezone(UTC)
    tomorrow_start = datetime.combine(today + timedelta(days=1), time.min, MOSCOW).astimezone(UTC)
    first_day = today - timedelta(days=13)

    async with session_factory() as session:
        total_groups = await session.scalar(
            select(func.count()).select_from(StudyGroup).where(StudyGroup.is_active.is_(True))
        )
        total_students = await session.scalar(
            select(func.count())
            .select_from(ChatMember)
            .join(VkChat, VkChat.id == ChatMember.chat_id)
            .join(StudyGroup, StudyGroup.id == VkChat.study_group_id)
            .where(
                ChatMember.role == "student",
                ChatMember.is_active.is_(True),
                VkChat.is_active.is_(True),
                StudyGroup.is_active.is_(True),
            )
        )
        active_broadcasts = await session.scalar(
            select(func.count()).select_from(Broadcast).where(Broadcast.deadline >= now)
        )
        completed_broadcasts = await session.scalar(
            select(func.count()).select_from(Broadcast).where(Broadcast.deadline < now)
        )
        responses_today = await session.scalar(
            select(func.count())
            .select_from(BroadcastResponse)
            .where(
                BroadcastResponse.responded_at >= today_start,
                BroadcastResponse.responded_at < tomorrow_start,
            )
        )

        response_day = cast(
            func.timezone("Europe/Moscow", BroadcastResponse.responded_at),
            Date,
        ).label("day")
        response_rows = (
            await session.execute(
                select(response_day, func.count().label("count"))
                .where(BroadcastResponse.responded_at >= datetime.combine(first_day, time.min, MOSCOW).astimezone(UTC))
                .group_by(response_day)
                .order_by(response_day)
            )
        ).mappings()
        responses_by_date = {row["day"]: row["count"] for row in response_rows}

        broadcast_rows = list(
            (
                await session.execute(
                select(
                    Broadcast.id,
                    Broadcast.title,
                    Broadcast.deadline,
                    func.count(BroadcastRecipient.vk_user_id).label("recipient_count"),
                    func.count(BroadcastResponse.id).label("response_count"),
                )
                .select_from(Broadcast)
                .outerjoin(BroadcastTarget, BroadcastTarget.broadcast_id == Broadcast.id)
                .outerjoin(BroadcastRecipient, BroadcastRecipient.target_id == BroadcastTarget.id)
                .outerjoin(
                    BroadcastResponse,
                    and_(
                        BroadcastResponse.target_id == BroadcastRecipient.target_id,
                        BroadcastResponse.vk_user_id == BroadcastRecipient.vk_user_id,
                    ),
                )
                .group_by(Broadcast.id)
                .order_by(Broadcast.created_at.desc())
                .limit(8)
                )
            ).mappings()
        )

        students_by_group = (
            select(
                VkChat.study_group_id.label("group_id"),
                func.count(ChatMember.vk_user_id).label("student_count"),
            )
            .join(ChatMember, ChatMember.chat_id == VkChat.id)
            .where(ChatMember.role == "student", ChatMember.is_active.is_(True))
            .group_by(VkChat.study_group_id)
            .subquery()
        )
        recipients_by_group = (
            select(
                BroadcastTarget.study_group_id.label("group_id"),
                func.count(BroadcastRecipient.vk_user_id).label("recipient_count"),
            )
            .join(BroadcastRecipient, BroadcastRecipient.target_id == BroadcastTarget.id)
            .group_by(BroadcastTarget.study_group_id)
            .subquery()
        )
        responses_by_group = (
            select(
                BroadcastTarget.study_group_id.label("group_id"),
                func.count(BroadcastResponse.id).label("response_count"),
            )
            .join(BroadcastResponse, BroadcastResponse.target_id == BroadcastTarget.id)
            .group_by(BroadcastTarget.study_group_id)
            .subquery()
        )
        group_rows = list(
            (
                await session.execute(
                select(
                    StudyGroup.id,
                    StudyGroup.name,
                    func.coalesce(students_by_group.c.student_count, 0).label("student_count"),
                    func.coalesce(recipients_by_group.c.recipient_count, 0).label("recipient_count"),
                    func.coalesce(responses_by_group.c.response_count, 0).label("response_count"),
                )
                .outerjoin(students_by_group, students_by_group.c.group_id == StudyGroup.id)
                .outerjoin(recipients_by_group, recipients_by_group.c.group_id == StudyGroup.id)
                .outerjoin(responses_by_group, responses_by_group.c.group_id == StudyGroup.id)
                .where(StudyGroup.is_active.is_(True))
                .order_by(StudyGroup.name)
                )
            ).mappings()
        )

    return {
        "overview": {
            "total_groups": total_groups or 0,
            "total_students": total_students or 0,
            "active_broadcasts": active_broadcasts or 0,
            "completed_broadcasts": completed_broadcasts or 0,
            "responses_today": responses_today or 0,
        },
        "responses_over_time": [
            {"date": day, "count": responses_by_date.get(day, 0)}
            for day in (first_day + timedelta(days=offset) for offset in range(14))
        ],
        "broadcast_completion": [dict(row) for row in broadcast_rows],
        "group_activity": [dict(row) for row in group_rows],
    }
