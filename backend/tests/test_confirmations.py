import json

from app.integrations.vk.confirmations import parse_confirmation
from app.services.responses import confirmation_matches


def test_parse_confirmation_requires_reply_to_current_group() -> None:
    update = {
        "type": "message_new",
        "object": {
            "message": {
                "peer_id": 2_000_000_001,
                "from_id": 123,
                "id": 0,
                "conversation_message_id": 42,
                "date": 1_784_000_000,
                "text": "Готово",
                "attachments": [{"type": "photo", "photo": {"id": 1}}],
                "reply_message": {
                    "from_id": -7,
                    "payload": json.dumps({"broadcast_token": "token"}),
                },
            }
        },
    }

    confirmation = parse_confirmation(update, group_id=7)

    assert confirmation is not None
    assert confirmation.broadcast_token == "token"
    assert confirmation.conversation_message_id == 42
    assert parse_confirmation(update, group_id=8) is None


def test_confirmation_type_checks_photo() -> None:
    assert confirmation_matches("any_message", [])
    assert not confirmation_matches("image", [{"type": "doc"}])
    assert confirmation_matches("image", [{"type": "photo"}])
