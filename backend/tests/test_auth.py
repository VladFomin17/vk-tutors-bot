from fastapi.testclient import TestClient
from pydantic import SecretStr
from pytest import MonkeyPatch

from app.api import auth
from app.core.config import Settings
from app.main import app


def test_login_sets_http_only_session_cookie(monkeypatch: MonkeyPatch) -> None:
    settings = Settings(
        _env_file=None,
        admin_bootstrap_username="leader",
        admin_bootstrap_password=SecretStr("correct-password"),
    )

    async def fake_create_session() -> str:
        return "opaque-token"

    monkeypatch.setattr(auth, "get_settings", lambda: settings)
    monkeypatch.setattr(auth, "create_session", fake_create_session)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "leader", "password": "correct-password"},
        )

    assert response.status_code == 204
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "opaque-token" in cookie


def test_login_rejects_invalid_credentials(monkeypatch: MonkeyPatch) -> None:
    settings = Settings(
        _env_file=None,
        admin_bootstrap_username="leader",
        admin_bootstrap_password=SecretStr("correct-password"),
    )
    monkeypatch.setattr(auth, "get_settings", lambda: settings)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "leader", "password": "wrong-password"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
