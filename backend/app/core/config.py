from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_timezone: str = "Europe/Moscow"
    log_level: str = "INFO"
    database_url: str = (
        "postgresql+asyncpg://vk_tutors:vk_tutors@localhost:5432/vk_tutors"
    )
    admin_bootstrap_username: str = Field(default="admin", min_length=1, max_length=100)
    admin_bootstrap_password: SecretStr | None = None
    session_cookie_name: str = Field(default="vk_tutors_session", min_length=1, max_length=100)
    session_ttl_hours: int = Field(default=12, ge=1, le=168)
    session_cookie_secure: bool = False
    vk_group_id: int | None = Field(default=None, gt=0)
    vk_access_token: SecretStr | None = None
    vk_api_version: str = "5.199"
    vk_long_poll_wait_seconds: int = Field(default=25, ge=1, le=90)
    vk_request_timeout_seconds: int = Field(default=10, ge=1, le=60)
    vk_max_retries: int = Field(default=5, ge=1, le=10)
    outbox_poll_seconds: int = Field(default=10, ge=1, le=60)
    outbox_batch_size: int = Field(default=20, ge=1, le=100)
    outbox_max_attempts: int = Field(default=5, ge=1, le=20)

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
