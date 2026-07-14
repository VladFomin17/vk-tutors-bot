from datetime import datetime
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import Select

from app.db.session import session_factory
from app.models import (
    Broadcast,
    BroadcastRecipient,
    BroadcastResponse,
    BroadcastTarget,
    OutboundMessage,
    StudyGroup,
    VkChat,
    VkUser,
)


class BroadcastNotFoundError(RuntimeError):
    pass


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
) -> str:
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
            return "ignored"
        if not confirmation_matches(destination["confirmation_type"], attachments):
            return "wrong_type"

        response_id = await session.scalar(
            insert(BroadcastResponse)
            .values(
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
            .on_conflict_do_nothing()
            .returning(BroadcastResponse.id)
        )
        return "accepted" if response_id is not None else "duplicate"


async def list_results(broadcast_id: int) -> list[dict[str, object]]:
    async with session_factory() as session:
        exists = await session.scalar(select(Broadcast.id).where(Broadcast.id == broadcast_id))
        if exists is None:
            raise BroadcastNotFoundError("Broadcast not found")
        rows = await session.execute(_results_query(broadcast_id))
        return [
            {
                **dict(row),
                "id": f"{row['target_id']}:{row['vk_user_id']}",
                "responded": row["responded_at"] is not None,
                "attachments": row["attachments"] or [],
            }
            for row in rows.mappings()
        ]


def _results_query(broadcast_id: int) -> Select[Any]:
    return (
        select(
            BroadcastTarget.id.label("target_id"),
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
