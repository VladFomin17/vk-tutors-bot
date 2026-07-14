from app.integrations.vk.listener import parse_chat_message


def test_parse_chat_message_accepts_only_chat_messages() -> None:
    assert parse_chat_message(
        {
            "type": "message_new",
            "object": {"message": {"peer_id": 2_000_000_001, "from_id": 123}},
        }
    ) == (2_000_000_001, 123)
    assert parse_chat_message(
        {"type": "message_new", "object": {"message": {"peer_id": 123, "from_id": 123}}}
    ) is None
    assert parse_chat_message({"type": "message_reply"}) is None
