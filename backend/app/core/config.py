from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_timezone: str = "Europe/Moscow"
    log_level: str = "INFO"
    database_url: str = (
        "postgresql+asyncpg://vk_tutors:vk_tutors@localhost:5432/vk_tutors"
    )

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
