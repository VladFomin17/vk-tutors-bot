from datetime import UTC, datetime

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api import broadcasts
from app.main import app
from app.services.auth import require_admin


def test_broadcasts_require_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/broadcasts")

    assert response.status_code == 401


def test_create_broadcast_normalizes_payload(monkeypatch: MonkeyPatch) -> None:
    received: dict[str, object] = {}
    created_at = datetime.now(UTC)

    async def fake_create(**payload: object) -> dict[str, object]:
        received.update(payload)
        return {
            "id": 1,
            **payload,
            "created_at": created_at,
            "target_count": 1,
            "recipient_count": 2,
        }

    app.dependency_overrides[require_admin] = lambda: None
    monkeypatch.setattr(broadcasts.broadcasts, "create_broadcast", fake_create)
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/broadcasts",
                json={
                    "title": "  Опрос  ",
                    "message_text": "  Ответьте на вопросы  ",
                    "link": "https://example.com/form",
                    "deadline": "2026-07-20T18:00:00+03:00",
                    "confirmation_type": "any_message",
                    "study_group_ids": [1],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert received["title"] == "Опрос"
    assert received["message_text"] == "Ответьте на вопросы"


def test_create_broadcast_rejects_duplicate_groups() -> None:
    app.dependency_overrides[require_admin] = lambda: None
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/broadcasts",
                json={
                    "title": "Опрос",
                    "message_text": "Ответьте",
                    "deadline": "2026-07-20T18:00:00+03:00",
                    "confirmation_type": "image",
                    "study_group_ids": [1, 1],
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_delete_broadcast(monkeypatch: MonkeyPatch) -> None:
    async def fake_delete(broadcast_id: int) -> str | None:
        return "Опрос" if broadcast_id == 7 else None

    app.dependency_overrides[require_admin] = lambda: None
    monkeypatch.setattr(broadcasts.broadcasts, "delete_broadcast", fake_delete)
    try:
        with TestClient(app) as client:
            deleted = client.delete("/api/v1/broadcasts/7")
            missing = client.delete("/api/v1/broadcasts/8")
    finally:
        app.dependency_overrides.clear()

    assert deleted.status_code == 204
    assert missing.status_code == 404


def _delivery_stage(status: str = "failed") -> dict[str, object]:
    return {
        "id": 11,
        "kind": "initial",
        "status": status,
        "attempt_count": 5,
        "scheduled_at": "2026-07-20T10:00:00+00:00",
        "sent_at": None,
        "last_error": "VK unavailable",
        "can_retry": status == "failed",
    }


def test_get_broadcast_deliveries(monkeypatch: MonkeyPatch) -> None:
    async def fake_list(broadcast_id: int) -> list[dict[str, object]]:
        assert broadcast_id == 7
        return [
            {
                "id": 3,
                "study_group_name": "101",
                "chat_title": "Учебная беседа",
                "peer_id": 2_000_000_001,
                "initial": _delivery_stage(),
                "reminder": None,
            }
        ]

    app.dependency_overrides[require_admin] = lambda: None
    monkeypatch.setattr(broadcasts.outbox, "list_deliveries", fake_list)
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/broadcasts/7/deliveries")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["initial"]["attempt_count"] == 5
    assert response.json()[0]["reminder"] is None


def test_retry_failed_delivery(monkeypatch: MonkeyPatch) -> None:
    async def fake_retry(broadcast_id: int, outbound_id: int) -> dict[str, object]:
        assert (broadcast_id, outbound_id) == (7, 11)
        return _delivery_stage("pending")

    app.dependency_overrides[require_admin] = lambda: None
    monkeypatch.setattr(broadcasts.outbox, "retry_failed", fake_retry)
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/broadcasts/7/deliveries/11/retry")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_retry_rejects_non_failed_delivery(monkeypatch: MonkeyPatch) -> None:
    async def fake_retry(*_: int) -> dict[str, object]:
        raise broadcasts.outbox.OutboundRetryConflictError(
            "Only failed messages can be retried"
        )

    app.dependency_overrides[require_admin] = lambda: None
    monkeypatch.setattr(broadcasts.outbox, "retry_failed", fake_retry)
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/broadcasts/7/deliveries/11/retry")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
