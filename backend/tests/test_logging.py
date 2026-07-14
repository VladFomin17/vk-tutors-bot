import json
import logging
import sys

from app.core.logging import JsonFormatter


def test_json_formatter_includes_exception() -> None:
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=10,
            msg="failed",
            args=(),
            exc_info=exc_info,
        )

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "failed"
    assert "RuntimeError: boom" in payload["exception"]
