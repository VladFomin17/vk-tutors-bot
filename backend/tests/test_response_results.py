from sqlalchemy.dialects import postgresql

from app.services.responses import _response_upsert, _results_query


def test_results_query_has_explicit_recipient_source() -> None:
    sql = str(_results_query(1).compile(dialect=postgresql.dialect()))

    assert "FROM broadcast_recipients JOIN broadcast_targets" in sql


def test_newer_confirmation_replaces_previous_response() -> None:
    sql = str(
        _response_upsert(
            target_id=1,
            outbound_message_id=1,
            vk_user_id=1,
            peer_id=2_000_000_001,
            vk_message_id=0,
            conversation_message_id=2,
            text="Исправлено",
            attachments=[],
            responded_at="2026-07-14T12:00:00+00:00",
            is_late=False,
        ).compile(dialect=postgresql.dialect())
    )

    assert "ON CONFLICT ON CONSTRAINT uq_broadcast_responses_recipient DO UPDATE" in sql
    assert "excluded.conversation_message_id > broadcast_responses.conversation_message_id" in sql
