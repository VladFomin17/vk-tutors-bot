import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.auth import create_session, require_admin, revoke_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login(credentials: LoginRequest, response: Response) -> None:
    settings = get_settings()
    configured_password = settings.admin_bootstrap_password
    if configured_password is None or not configured_password.get_secret_value():
        logger.error("Administrator password is not configured")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Administrator authentication is not configured",
        )

    valid_username = secrets.compare_digest(
        credentials.username,
        settings.admin_bootstrap_username,
    )
    valid_password = secrets.compare_digest(
        credentials.password,
        configured_password.get_secret_value(),
    )
    if not valid_username or not valid_password:
        logger.warning("Administrator login failed")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    token = await create_session()
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    logger.info("Administrator login succeeded")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> None:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if token is not None:
        await revoke_session(token)
    response.delete_cookie(
        settings.session_cookie_name,
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
        path="/",
    )
    logger.info("Administrator logout succeeded")


@router.get("/session", dependencies=[Depends(require_admin)])
async def session_status() -> dict[str, bool]:
    return {"authenticated": True}
