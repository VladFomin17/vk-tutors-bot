import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class ConfirmationEvent:
    peer_id: int
    vk_user_id: int
    vk_message_id: int
    conversation_message_id: int
    responded_at: datetime
    text: str
    attachments: list[dict[str, object]]
    broadcast_token: str


def parse_confirmation(
    update: dict[str, Any],
    group_id: int,
) -> ConfirmationEvent | None:
    if update.get("type") != "message_new":
        return None
    event_object = update.get("object")
    message = event_object.get("message") if isinstance(event_object, dict) else None
    if not isinstance(message, dict):
        return None
    reply = message.get("reply_message")
    if not isinstance(reply, dict) or reply.get("from_id") != -group_id:
        return None
    token = _read_token(reply.get("payload"))
    if token is None:
        return None

    peer_id = message.get("peer_id")
    vk_user_id = message.get("from_id")
    vk_message_id = message.get("id")
    conversation_message_id = message.get("conversation_message_id")
    timestamp = message.get("date")
    text = message.get("text")
    attachments = message.get("attachments", [])
    if not (
        isinstance(peer_id, int)
        and peer_id >= 2_000_000_000
        and isinstance(vk_user_id, int)
        and vk_user_id > 0
        and isinstance(vk_message_id, int)
        and isinstance(conversation_message_id, int)
        and conversation_message_id > 0
        and isinstance(timestamp, int)
        and timestamp > 0
        and isinstance(text, str)
        and isinstance(attachments, list)
    ):
        return None
    try:
        responded_at = datetime.fromtimestamp(timestamp, UTC)
    except (OverflowError, OSError, ValueError):
        return None
    return ConfirmationEvent(
        peer_id=peer_id,
        vk_user_id=vk_user_id,
        vk_message_id=vk_message_id,
        conversation_message_id=conversation_message_id,
        responded_at=responded_at,
        text=text,
        attachments=[attachment for attachment in attachments if isinstance(attachment, dict)],
        broadcast_token=token,
    )


def _read_token(payload: object) -> str | None:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return None
    if not isinstance(payload, dict):
        return None
    token = payload.get("broadcast_token")
    if not isinstance(token, str) or not token or len(token) > 64:
        return None
    return token
