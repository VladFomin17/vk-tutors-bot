import json

from app.integrations.vk.confirmations import parse_confirmation, parse_outbound_message
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


def test_parse_reaction_confirmation() -> None:
    update = {
        "type": "message_reaction_event",
        "object": {
            "peer_id": 2_000_000_001,
            "cmid": 42,
            "reacted_user_id": 123,
            "reaction_id": 1,
        },
    }

    confirmation = parse_confirmation(update, group_id=7)

    assert confirmation is not None
    assert confirmation.broadcast_token is None
    assert confirmation.conversation_message_id == 42
    assert confirmation.vk_user_id == 123
    update["object"]["reaction_id"] = 0
    assert parse_confirmation(update, group_id=7) is None


def test_parse_outbound_message_for_reaction_lookup() -> None:
    update = {
        "type": "message_reply",
        "object": {
            "message": {
                "from_id": -7,
                "id": 0,
                "conversation_message_id": 42,
                "payload": json.dumps({"broadcast_token": "token"}),
            }
        },
    }

    outbound = parse_outbound_message(update, group_id=7)

    assert outbound is not None
    assert outbound.broadcast_token == "token"
    assert outbound.conversation_message_id == 42
    assert parse_outbound_message(update, group_id=8) is None
