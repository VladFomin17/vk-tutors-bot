from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.directory import router as directory_router
from app.api.health import router as health_router
from app.core.logging import configure_logging
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    yield
    await engine.dispose()


app = FastAPI(title="VK Tutors Bot API", version="0.1.0", lifespan=lifespan)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(directory_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
