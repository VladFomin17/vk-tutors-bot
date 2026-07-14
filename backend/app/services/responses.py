from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import and_, delete, select
from sqlalchemy.dialects.postgresql import Insert, insert
from sqlalchemy.sql import Select

from app.db.session import session_factory
from app.models import (
    Broadcast,
    BroadcastRecipient,
    BroadcastResponse,
    BroadcastTarget,
    OutboundMessage,
    ResponseMedia,
    StudyGroup,
    VkChat,
    VkUser,
)
from app.services.media import MediaJob


class BroadcastNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class ConfirmationResult:
    status: str
    media_job: MediaJob | None = None
    obsolete_storage_names: tuple[str, ...] = ()


def confirmation_matches(
    confirmation_type: str,
    attachments: list[dict[str, object]],
) -> bool:
    return confirmation_type == "any_message" or any(
        attachment.get("type") == "photo" for attachment in attachments
    )


async def record_confirmation(
    *,
    peer_id: int,
    vk_user_id: int,
    vk_message_id: int,
    conversation_message_id: int,
    responded_at: datetime,
    text: str,
    attachments: list[dict[str, object]],
    broadcast_token: str,
) -> ConfirmationResult:
    async with session_factory.begin() as session:
        destination = (
            await session.execute(
                select(
                    OutboundMessage.id.label("outbound_message_id"),
                    BroadcastTarget.id.label("target_id"),
                    Broadcast.confirmation_type,
                    Broadcast.deadline,
                )
                .join(BroadcastTarget, BroadcastTarget.id == OutboundMessage.target_id)
                .join(VkChat, VkChat.id == BroadcastTarget.chat_id)
                .join(Broadcast, Broadcast.id == BroadcastTarget.broadcast_id)
                .join(
                    BroadcastRecipient,
                    and_(
                        BroadcastRecipient.target_id == BroadcastTarget.id,
                        BroadcastRecipient.vk_user_id == vk_user_id,
                    ),
                )
                .where(
                    OutboundMessage.broadcast_token == broadcast_token,
                    VkChat.peer_id == peer_id,
                )
            )
        ).mappings().one_or_none()
        if destination is None:
            return ConfirmationResult("ignored")
        if not confirmation_matches(destination["confirmation_type"], attachments):
            return ConfirmationResult("wrong_type")

        response_id = await session.scalar(
            _response_upsert(
                target_id=destination["target_id"],
                outbound_message_id=destination["outbound_message_id"],
                vk_user_id=vk_user_id,
                peer_id=peer_id,
                vk_message_id=vk_message_id,
                conversation_message_id=conversation_message_id,
                text=text,
                attachments=attachments,
                responded_at=responded_at,
                is_late=responded_at > destination["deadline"],
            )
            .returning(BroadcastResponse.id)
        )
        if response_id is not None:
            old_names = tuple(
                await session.scalars(
                    select(ResponseMedia.storage_name).where(
                        ResponseMedia.response_id == response_id
                    )
                )
            )
            await session.execute(
                delete(ResponseMedia).where(ResponseMedia.response_id == response_id)
            )
            return ConfirmationResult(
                "accepted",
                MediaJob(response_id, conversation_message_id, attachments),
                old_names,
            )

        existing = (
            await session.execute(
                select(BroadcastResponse.id, BroadcastResponse.conversation_message_id).where(
                    BroadcastResponse.target_id == destination["target_id"],
                    BroadcastResponse.vk_user_id == vk_user_id,
                )
            )
        ).one()
        job = (
            MediaJob(existing.id, conversation_message_id, attachments)
            if existing.conversation_message_id == conversation_message_id
            else None
        )
        return ConfirmationResult("duplicate" if job is not None else "outdated", job)


def _response_upsert(**values: object) -> Insert:
    statement = insert(BroadcastResponse).values(**values)
    return statement.on_conflict_do_update(
        constraint="uq_broadcast_responses_recipient",
        set_={
            "outbound_message_id": statement.excluded.outbound_message_id,
            "peer_id": statement.excluded.peer_id,
            "vk_message_id": statement.excluded.vk_message_id,
            "conversation_message_id": statement.excluded.conversation_message_id,
            "text": statement.excluded.text,
            "attachments": statement.excluded.attachments,
            "responded_at": statement.excluded.responded_at,
            "is_late": statement.excluded.is_late,
        },
        where=(
            statement.excluded.conversation_message_id
            > BroadcastResponse.conversation_message_id
        ),
    )


async def list_results(broadcast_id: int) -> list[dict[str, object]]:
    async with session_factory() as session:
        exists = await session.scalar(select(Broadcast.id).where(Broadcast.id == broadcast_id))
        if exists is None:
            raise BroadcastNotFoundError("Broadcast not found")
        rows = list((await session.execute(_results_query(broadcast_id))).mappings())
        response_ids = [row["response_id"] for row in rows if row["response_id"] is not None]
        media_by_response: dict[int, list[dict[str, object]]] = {}
        if response_ids:
            media_rows = (
                await session.execute(
                    select(
                        ResponseMedia.id,
                        ResponseMedia.response_id,
                        ResponseMedia.content_type,
                        ResponseMedia.size_bytes,
                    )
                    .where(ResponseMedia.response_id.in_(response_ids))
                    .order_by(ResponseMedia.response_id, ResponseMedia.position)
                )
            ).mappings()
            for media in media_rows:
                media_by_response.setdefault(media["response_id"], []).append(
                    {
                        "id": media["id"],
                        "content_type": media["content_type"],
                        "size_bytes": media["size_bytes"],
                    }
                )
        return [
            {
                **dict(row),
                "id": f"{row['target_id']}:{row['vk_user_id']}",
                "responded": row["responded_at"] is not None,
                "attachments": row["attachments"] or [],
                "media": media_by_response.get(row["response_id"], []),
            }
            for row in rows
        ]


def _results_query(broadcast_id: int) -> Select[Any]:
    return (
        select(
            BroadcastTarget.id.label("target_id"),
            BroadcastResponse.id.label("response_id"),
            StudyGroup.name.label("study_group_name"),
            VkUser.vk_user_id,
            VkUser.first_name,
            VkUser.last_name,
            BroadcastResponse.text,
            BroadcastResponse.attachments,
            BroadcastResponse.responded_at,
            BroadcastResponse.is_late,
        )
        .select_from(BroadcastRecipient)
        .join(BroadcastTarget, BroadcastTarget.id == BroadcastRecipient.target_id)
        .join(StudyGroup, StudyGroup.id == BroadcastTarget.study_group_id)
        .join(VkUser, VkUser.vk_user_id == BroadcastRecipient.vk_user_id)
        .outerjoin(
            BroadcastResponse,
            and_(
                BroadcastResponse.target_id == BroadcastRecipient.target_id,
                BroadcastResponse.vk_user_id == BroadcastRecipient.vk_user_id,
            ),
        )
        .where(BroadcastTarget.broadcast_id == broadcast_id)
        .order_by(StudyGroup.name, VkUser.last_name, VkUser.first_name)
    )
