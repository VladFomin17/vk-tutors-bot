from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.exc import SQLAlchemyError

from app.api import health
from app.main import app


def test_live() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_503_without_database(monkeypatch: MonkeyPatch) -> None:
    async def unavailable_database() -> None:
        raise SQLAlchemyError("offline")

    monkeypatch.setattr(health, "check_database", unavailable_database)

    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable"}
