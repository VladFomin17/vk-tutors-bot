import asyncio
import logging
import signal
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.session import engine
from app.integrations.vk.client import VkClient, build_client
from app.services import outbox

logger = logging.getLogger(__name__)


def format_message(job: outbox.OutboundJob) -> str:
    prefix = "@all\n\n" if job.kind == "initial" else "@all\n\nНапоминание:\n"
    parts = [f"{prefix}{job.message_text}"]
    if job.link:
        parts.append(job.link)
    return "\n\n".join(parts)


async def process_due_messages(client: VkClient, settings: Settings) -> None:
    jobs = await outbox.claim_due(settings.outbox_batch_size)
    if jobs:
        logger.info("Outbox scheduler claimed %s messages", len(jobs))
    for job in jobs:
        try:
            vk_message_id = await client.send_message(
                peer_id=job.peer_id,
                random_id=job.random_id,
                message=format_message(job),
                broadcast_token=job.broadcast_token,
            )
            await outbox.mark_sent(job.id, vk_message_id)
            logger.info("Outbound message %s sent", job.id)
        except Exception as error:
            logger.exception("Outbound message %s failed", job.id)
            await outbox.mark_failed(job, error, settings.outbox_max_attempts)


async def run() -> None:
    settings = get_settings()
    client = build_client(settings)
    recovered = await outbox.recover_interrupted()
    if recovered:
        logger.info("Recovered %s interrupted outbox messages", recovered)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for shutdown_signal in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(shutdown_signal, stop_event.set)

    scheduler = AsyncIOScheduler(timezone=UTC)
    scheduler.add_job(
        process_due_messages,
        "interval",
        args=(client, settings),
        seconds=settings.outbox_poll_seconds,
        next_run_time=datetime.now(UTC),
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("Outbox worker started")
    try:
        await stop_event.wait()
    finally:
        scheduler.shutdown(wait=True)
        await engine.dispose()
        logger.info("Outbox worker stopped")


if __name__ == "__main__":
    configure_logging()
    logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)
    asyncio.run(run())
