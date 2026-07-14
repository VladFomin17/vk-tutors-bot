from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.db.session import session_factory
from app.models import Broadcast, BroadcastTarget, OutboundMessage, VkChat


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
        await session.execute(
            update(OutboundMessage)
            .where(OutboundMessage.status == "processing")
            .values(status="pending", scheduled_at=now)
        )
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
