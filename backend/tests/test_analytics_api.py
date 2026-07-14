from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api import analytics
from app.main import app
from app.services.auth import require_admin


def test_analytics_requires_authentication() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/students").status_code == 401
        assert client.get("/api/v1/statistics").status_code == 401


def test_students_return_group_context(monkeypatch: MonkeyPatch) -> None:
    now = datetime.now(UTC)

    async def fake_students() -> list[dict[str, object]]:
        return [{
            "id": "1:2",
            "chat_id": 1,
            "vk_user_id": 2,
            "first_name": "Иван",
            "last_name": "Иванов",
            "is_active": True,
            "first_seen_at": now,
            "last_seen_at": now,
            "study_group_id": 3,
            "study_group_name": "ИВТ-101",
            "chat_title": "ИВТ-101 чат",
        }]

    app.dependency_overrides[require_admin] = lambda: None
    monkeypatch.setattr(analytics.analytics, "list_students", fake_students)
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/students")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["study_group_name"] == "ИВТ-101"


def test_statistics_response_is_typed(monkeypatch: MonkeyPatch) -> None:
    async def fake_statistics() -> dict[str, object]:
        return {
            "overview": {
                "total_groups": 1,
                "total_students": 2,
                "active_broadcasts": 1,
                "completed_broadcasts": 0,
                "responses_today": 1,
            },
            "responses_over_time": [{"date": date(2026, 7, 14), "count": 1}],
            "broadcast_completion": [],
            "group_activity": [],
        }

    app.dependency_overrides[require_admin] = lambda: None
    monkeypatch.setattr(analytics.analytics, "get_statistics", fake_statistics)
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/statistics")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["overview"]["responses_today"] == 1
