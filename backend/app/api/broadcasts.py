import logging
from datetime import datetime
from io import BytesIO
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl, field_validator
from starlette.responses import StreamingResponse

from app.services import broadcasts
from app.services import exports
from app.services import responses
from app.services.auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(tags=["broadcasts"], dependencies=[Depends(require_admin)])


class BroadcastCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    message_text: str = Field(min_length=1, max_length=10000)
    link: HttpUrl | None = None
    deadline: datetime
    confirmation_type: Literal["any_message", "image"]
    study_group_ids: list[int] = Field(min_length=1)

    @field_validator("title", "message_text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value must not be blank")
        return normalized

    @field_validator("deadline")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("Deadline must include a timezone")
        return value

    @field_validator("study_group_ids")
    @classmethod
    def require_unique_group_ids(cls, value: list[int]) -> list[int]:
        if any(group_id <= 0 for group_id in value):
            raise ValueError("Study group IDs must be positive")
        if len(value) != len(set(value)):
            raise ValueError("Study group IDs must be unique")
        return value


class BroadcastSummaryResponse(BaseModel):
    id: int
    title: str
    message_text: str
    link: str | None
    deadline: datetime
    confirmation_type: Literal["any_message", "image"]
    created_at: datetime
    target_count: int
    recipient_count: int


class BroadcastResultResponse(BaseModel):
    id: str
    target_id: int
    study_group_name: str
    vk_user_id: int
    first_name: str
    last_name: str
    responded: bool
    text: str | None
    attachments: list[dict[str, Any]]
    responded_at: datetime | None
    is_late: bool | None


@router.get("/broadcasts", response_model=list[BroadcastSummaryResponse])
async def get_broadcasts() -> list[dict[str, object]]:
    return await broadcasts.list_broadcasts()


@router.get("/broadcasts/{broadcast_id}/results", response_model=list[BroadcastResultResponse])
async def get_broadcast_results(broadcast_id: int) -> list[dict[str, object]]:
    try:
        return await responses.list_results(broadcast_id)
    except responses.BroadcastNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error


@router.get("/broadcasts/{broadcast_id}/export.{file_type}")
async def export_broadcast_results(
    broadcast_id: int,
    file_type: Literal["xlsx", "docx"],
) -> StreamingResponse:
    try:
        results = await responses.list_results(broadcast_id)
    except responses.BroadcastNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    title = await broadcasts.get_broadcast_title(broadcast_id)
    if title is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Broadcast not found")
    content = (
        exports.create_xlsx(title, results)
        if file_type == "xlsx"
        else exports.create_docx(results)
    )
    media_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if file_type == "xlsx"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    logger.info("Broadcast %s results exported as %s", broadcast_id, file_type)
    return StreamingResponse(
        BytesIO(content),
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="broadcast-{broadcast_id}-results.{file_type}"'
            )
        },
    )


@router.post(
    "/broadcasts",
    response_model=BroadcastSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_broadcast(payload: BroadcastCreate) -> dict[str, object]:
    try:
        broadcast = await broadcasts.create_broadcast(
            title=payload.title,
            message_text=payload.message_text,
            link=str(payload.link) if payload.link else None,
            deadline=payload.deadline,
            confirmation_type=payload.confirmation_type,
            study_group_ids=payload.study_group_ids,
        )
    except broadcasts.BroadcastConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    logger.info("Broadcast %s created", broadcast["id"])
    return broadcast
