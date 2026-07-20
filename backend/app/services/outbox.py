from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.db.session import session_factory
from app.models import Broadcast, BroadcastTarget, OutboundMessage, StudyGroup, VkChat


class OutboundNotFoundError(RuntimeError):
    pass


class OutboundRetryConflictError(RuntimeError):
    pass


@dataclass(frozen=True)
class OutboundJob:
    id: int
    peer_id: int
    kind: str
    message_text: str
    link: str | None
    random_id: int
    broadcast_token: str
    attempt_count: int


async def claim_due(batch_size: int) -> list[OutboundJob]:
    now = datetime.now(UTC)
    async with session_factory.begin() as session:
        rows = (
            await session.execute(
                select(
                    OutboundMessage,
                    VkChat.peer_id,
                    Broadcast.message_text,
                    Broadcast.link,
                    Broadcast.deadline,
                )
                .join(BroadcastTarget, BroadcastTarget.id == OutboundMessage.target_id)
                .join(VkChat, VkChat.id == BroadcastTarget.chat_id)
                .join(Broadcast, Broadcast.id == BroadcastTarget.broadcast_id)
                .where(
                    OutboundMessage.status == "pending",
                    OutboundMessage.scheduled_at <= now,
                )
                .order_by(OutboundMessage.scheduled_at, OutboundMessage.id)
                .limit(batch_size)
                .with_for_update(skip_locked=True)
            )
        ).all()

        jobs: list[OutboundJob] = []
        for outbound, peer_id, message_text, link, deadline in rows:
            if deadline <= now:
                outbound.status = "cancelled"
                continue
            outbound.status = "processing"
            outbound.attempt_count += 1
            outbound.last_error = None
            jobs.append(
                OutboundJob(
                    id=outbound.id,
                    peer_id=peer_id,
                    kind=outbound.kind,
                    message_text=message_text,
                    link=link,
                    random_id=outbound.random_id,
                    broadcast_token=outbound.broadcast_token,
                    attempt_count=outbound.attempt_count,
                )
            )
        return jobs


async def recover_interrupted() -> int:
    async with session_factory.begin() as session:
        result = await session.execute(
            update(OutboundMessage)
            .where(OutboundMessage.status == "processing")
            .values(status="pending", scheduled_at=datetime.now(UTC))
        )
        return result.rowcount


async def list_deliveries(broadcast_id: int) -> list[dict[str, object]]:
    now = datetime.now(UTC)
    async with session_factory() as session:
        if (
            await session.scalar(select(Broadcast.id).where(Broadcast.id == broadcast_id))
            is None
        ):
            raise OutboundNotFoundError("Broadcast not found")
        rows = (
            await session.execute(
                select(
                    OutboundMessage,
                    BroadcastTarget.id.label("target_id"),
                    StudyGroup.name.label("study_group_name"),
                    VkChat.title.label("chat_title"),
                    VkChat.peer_id,
                    Broadcast.deadline,
                )
                .join(BroadcastTarget, BroadcastTarget.id == OutboundMessage.target_id)
                .join(Broadcast, Broadcast.id == BroadcastTarget.broadcast_id)
                .join(StudyGroup, StudyGroup.id == BroadcastTarget.study_group_id)
                .join(VkChat, VkChat.id == BroadcastTarget.chat_id)
                .where(Broadcast.id == broadcast_id)
                .order_by(BroadcastTarget.id, OutboundMessage.kind)
            )
        ).all()

    deliveries: dict[int, dict[str, object]] = {}
    for outbound, target_id, study_group_name, chat_title, peer_id, deadline in rows:
        delivery = deliveries.setdefault(
            target_id,
            {
                "id": target_id,
                "study_group_name": study_group_name,
                "chat_title": chat_title,
                "peer_id": peer_id,
                "initial": None,
                "reminder": None,
            },
        )
        delivery[outbound.kind] = _delivery_stage(outbound, deadline, now)
    return list(deliveries.values())


async def retry_failed(broadcast_id: int, outbound_id: int) -> dict[str, object]:
    now = datetime.now(UTC)
    async with session_factory.begin() as session:
        row = (
            await session.execute(
                select(OutboundMessage, Broadcast.deadline)
                .join(BroadcastTarget, BroadcastTarget.id == OutboundMessage.target_id)
                .join(Broadcast, Broadcast.id == BroadcastTarget.broadcast_id)
                .where(
                    OutboundMessage.id == outbound_id,
                    Broadcast.id == broadcast_id,
                )
                .with_for_update()
            )
        ).one_or_none()
        if row is None:
            raise OutboundNotFoundError("Outbound message not found")
        outbound, deadline = row
        if outbound.status != "failed":
            raise OutboundRetryConflictError("Only failed messages can be retried")
        if deadline <= now:
            raise OutboundRetryConflictError("Broadcast deadline has passed")
        outbound.status = "pending"
        outbound.scheduled_at = now
        await session.flush()
        return _delivery_stage(outbound, deadline, now)


def _delivery_stage(
    outbound: OutboundMessage,
    deadline: datetime,
    now: datetime,
) -> dict[str, object]:
    return {
        "id": outbound.id,
        "kind": outbound.kind,
        "status": outbound.status,
        "attempt_count": outbound.attempt_count,
        "scheduled_at": outbound.scheduled_at,
        "sent_at": outbound.sent_at,
        "last_error": outbound.last_error,
        "can_retry": outbound.status == "failed" and deadline > now,
    }


async def mark_sent(job_id: int, vk_message_id: int) -> None:
    async with session_factory.begin() as session:
        await session.execute(
            update(OutboundMessage)
            .where(OutboundMessage.id == job_id, OutboundMessage.status == "processing")
            .values(
                status="sent",
                sent_at=datetime.now(UTC),
                vk_message_id=vk_message_id,
                last_error=None,
            )
        )


async def remember_delivery(
    *,
    vk_message_id: int,
    conversation_message_id: int,
    broadcast_token: str,
) -> None:
    async with session_factory.begin() as session:
        await session.execute(
            update(OutboundMessage)
            .where(OutboundMessage.broadcast_token == broadcast_token)
            .values(
                vk_message_id=vk_message_id,
                conversation_message_id=conversation_message_id,
            )
        )


async def mark_failed(job: OutboundJob, error: Exception, max_attempts: int) -> None:
    failed_permanently = job.attempt_count >= max_attempts
    values: dict[str, object] = {
        "status": "failed" if failed_permanently else "pending",
        "last_error": str(error)[:1000],
    }
    if not failed_permanently:
        values["scheduled_at"] = datetime.now(UTC) + timedelta(
            seconds=min(2**job.attempt_count, 300)
        )
    async with session_factory.begin() as session:
        await session.execute(
            update(OutboundMessage)
            .where(OutboundMessage.id == job.id, OutboundMessage.status == "processing")
            .values(**values)
        )
