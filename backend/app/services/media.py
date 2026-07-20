from dataclasses import dataclass
import logging
from pathlib import Path

from sqlalchemy import delete, select

from app.db.session import session_factory
from app.models import BroadcastResponse, ResponseMedia

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MediaFile:
    storage_name: str
    content_type: str
    size_bytes: int


@dataclass(frozen=True)
class MediaJob:
    response_id: int
    conversation_message_id: int
    attachments: list[dict[str, object]]


async def list_missing_media_jobs() -> list[MediaJob]:
    async with session_factory() as session:
        rows = (
            await session.execute(
                select(
                    BroadcastResponse.id,
                    BroadcastResponse.conversation_message_id,
                    BroadcastResponse.attachments,
                )
                .outerjoin(ResponseMedia, ResponseMedia.response_id == BroadcastResponse.id)
                .where(ResponseMedia.id.is_(None))
            )
        ).all()
        return [
            MediaJob(row.id, row.conversation_message_id, row.attachments)
            for row in rows
            if any(attachment.get("type") == "photo" for attachment in row.attachments)
        ]


async def replace_response_media(job: MediaJob, files: list[MediaFile]) -> list[str] | None:
    async with session_factory.begin() as session:
        current_message_id = await session.scalar(
            select(BroadcastResponse.conversation_message_id).where(
                BroadcastResponse.id == job.response_id
            )
        )
        if current_message_id != job.conversation_message_id:
            return None
        old_names = list(
            await session.scalars(
                select(ResponseMedia.storage_name).where(
                    ResponseMedia.response_id == job.response_id
                )
            )
        )
        await session.execute(
            delete(ResponseMedia).where(ResponseMedia.response_id == job.response_id)
        )
        session.add_all(
            ResponseMedia(
                response_id=job.response_id,
                position=position,
                storage_name=file.storage_name,
                content_type=file.content_type,
                size_bytes=file.size_bytes,
            )
            for position, file in enumerate(files)
        )
        return old_names


async def get_media(media_id: int) -> dict[str, object] | None:
    async with session_factory() as session:
        row = (
            await session.execute(
                select(
                    ResponseMedia.storage_name,
                    ResponseMedia.content_type,
                    ResponseMedia.size_bytes,
                ).where(ResponseMedia.id == media_id)
            )
        ).mappings().one_or_none()
        return dict(row) if row is not None else None


def remove_files(root: Path, storage_names: list[str]) -> None:
    resolved_root = root.resolve()
    for storage_name in storage_names:
        path = (resolved_root / storage_name).resolve()
        if not path.is_relative_to(resolved_root):
            logger.error("Refused to remove image outside media root: %s", storage_name)
            continue
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to remove stored image %s", storage_name, exc_info=True)
