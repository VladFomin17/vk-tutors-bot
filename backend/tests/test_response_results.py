from sqlalchemy.dialects import postgresql

from app.services.responses import _results_query


def test_results_query_has_explicit_recipient_source() -> None:
    sql = str(_results_query(1).compile(dialect=postgresql.dialect()))

    assert "FROM broadcast_recipients JOIN broadcast_targets" in sql
