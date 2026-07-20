from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api import directory
from app.main import app
from app.services.auth import require_admin


def test_directory_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/study-groups")

    assert response.status_code == 401


def test_create_study_group_normalizes_name(monkeypatch: MonkeyPatch) -> None:
    received_name: str | None = None

    async def fake_create(name: str) -> dict[str, object]:
        nonlocal received_name
        received_name = name
        return {"id": 1, "name": name, "is_active": True}

    app.dependency_overrides[require_admin] = lambda: None
    monkeypatch.setattr(directory.chat_directory, "create_study_group", fake_create)
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/study-groups", json={"name": "  ИВТ-101  "})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert received_name == "ИВТ-101"


def test_member_role_rejects_unknown_value() -> None:
    app.dependency_overrides[require_admin] = lambda: None
    try:
        with TestClient(app) as client:
            response = client.patch(
                "/api/v1/vk-chats/1/members/1",
                json={"role": "administrator"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_study_groups_include_activity_metrics(monkeypatch: MonkeyPatch) -> None:
    async def fake_groups() -> list[dict[str, object]]:
        return [
            {
                "id": 1,
                "name": "ИВТ-101",
                "is_active": True,
                "student_count": 20,
                "unknown_count": 2,
                "last_activity_at": "2026-07-20T12:00:00+00:00",
            }
        ]

    app.dependency_overrides[require_admin] = lambda: None
    monkeypatch.setattr(directory.chat_directory, "list_study_groups", fake_groups)
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/study-groups")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["student_count"] == 20
    assert response.json()[0]["unknown_count"] == 2
