import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, status
from sqlalchemy import delete, select

from app.core.config import get_settings
from app.db.session import session_factory
from app.models import AuthSession


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_session() -> str:
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    async with session_factory.begin() as session:
        await session.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
        session.add(
            AuthSession(
                token_hash=hash_token(token),
                expires_at=now + timedelta(hours=settings.session_ttl_hours),
            )
        )
    return token


async def revoke_session(token: str) -> None:
    async with session_factory.begin() as session:
        await session.execute(
            delete(AuthSession).where(AuthSession.token_hash == hash_token(token))
        )


async def require_admin(request: Request) -> None:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")

    async with session_factory() as session:
        token_hash = await session.scalar(
            select(AuthSession.token_hash).where(
                AuthSession.token_hash == hash_token(token),
                AuthSession.expires_at > datetime.now(UTC),
            )
        )
    if token_hash is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
