from pydantic import ValidationError
from pytest import raises

from app.core.config import Settings


def test_production_rejects_insecure_session_cookie() -> None:
    with raises(ValidationError, match="SESSION_COOKIE_SECURE"):
        Settings(
            _env_file=None,
            app_env="production",
            admin_bootstrap_password="a" * 32,
            postgres_password="b" * 32,
            database_url="postgresql+asyncpg://app:secret@postgres/app",
            vk_group_id=1,
            vk_access_token="token",
        )
