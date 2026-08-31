import logging
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.integrations.vk.chat_sync import sync_available_chats
from app.integrations.vk.client import VkApiError
from app.services import chat_directory
from app.services.auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(tags=["directory"], dependencies=[Depends(require_admin)])
MemberRole = Literal["unknown", "student", "tutor", "leader"]


class StudyGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Group name must not be blank")
        return normalized


class StudyGroupResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    student_count: int = 0
    unknown_count: int = 0
    last_activity_at: datetime | None = None


class ChatLinkUpdate(BaseModel):
    study_group_id: int | None = Field(default=None, gt=0)


class ChatResponse(BaseModel):
    id: int
    peer_id: int
    title: str | None
    study_group_id: int | None
    is_active: bool


class ChatSyncResponse(BaseModel):
    synchronized_count: int


class MemberRoleUpdate(BaseModel):
    role: MemberRole


class VkUserNameUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        return normalized or None


class VkUserNameResponse(BaseModel):
    vk_user_id: int
    full_name: str | None


class MemberResponse(BaseModel):
    id: str
    chat_id: int
    vk_user_id: int
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    role: MemberRole
    is_active: bool


class MemberRoleResponse(BaseModel):
    id: str
    chat_id: int
    vk_user_id: int
    role: MemberRole
    is_active: bool


def translate_directory_error(error: RuntimeError) -> HTTPException:
    if isinstance(error, chat_directory.DirectoryNotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, str(error))
    return HTTPException(status.HTTP_409_CONFLICT, str(error))


@router.get("/study-groups", response_model=list[StudyGroupResponse])
async def get_study_groups() -> list[dict[str, object]]:
    return await chat_directory.list_study_groups()


@router.post(
    "/study-groups",
    response_model=StudyGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_study_group(payload: StudyGroupCreate) -> dict[str, object]:
    try:
        group = await chat_directory.create_study_group(payload.name)
    except chat_directory.DirectoryConflictError as error:
        raise translate_directory_error(error) from error
    logger.info("Study group %s created", group["id"])
    return group


@router.get("/vk-chats", response_model=list[ChatResponse])
async def get_chats() -> list[dict[str, object]]:
    return await chat_directory.list_chats()


@router.post("/vk-chats/sync", response_model=ChatSyncResponse)
async def post_sync_chats() -> dict[str, int]:
    try:
        synchronized_count = await sync_available_chats()
    except (RuntimeError, VkApiError) as error:
        logger.exception("VK chat synchronization failed")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Не удалось синхронизировать беседы с VK",
        ) from error
    logger.info("VK chat synchronization completed: %s chats", synchronized_count)
    return {"synchronized_count": synchronized_count}


@router.patch("/vk-chats/{chat_id}", response_model=ChatResponse)
async def patch_chat(chat_id: int, payload: ChatLinkUpdate) -> dict[str, object]:
    try:
        chat = await chat_directory.link_chat(chat_id, payload.study_group_id)
    except (chat_directory.DirectoryNotFoundError, chat_directory.DirectoryConflictError) as error:
        raise translate_directory_error(error) from error
    logger.info("VK chat %s linked to study group %s", chat_id, payload.study_group_id)
    return chat


@router.get("/vk-chats/{chat_id}/members", response_model=list[MemberResponse])
async def get_members(chat_id: int) -> list[dict[str, object]]:
    try:
        return await chat_directory.list_members(chat_id)
    except chat_directory.DirectoryNotFoundError as error:
        raise translate_directory_error(error) from error


@router.patch(
    "/vk-chats/{chat_id}/members/{vk_user_id}",
    response_model=MemberRoleResponse,
)
async def patch_member_role(
    chat_id: int,
    vk_user_id: int,
    payload: MemberRoleUpdate,
) -> dict[str, object]:
    try:
        member = await chat_directory.update_member_role(chat_id, vk_user_id, payload.role)
    except chat_directory.DirectoryNotFoundError as error:
        raise translate_directory_error(error) from error
    logger.info("VK chat %s member role updated", chat_id)
    return member


@router.patch("/vk-users/{vk_user_id}", response_model=VkUserNameResponse)
async def patch_vk_user_name(
    vk_user_id: int,
    payload: VkUserNameUpdate,
) -> dict[str, object]:
    try:
        user = await chat_directory.update_user_full_name(vk_user_id, payload.full_name)
    except chat_directory.DirectoryNotFoundError as error:
        raise translate_directory_error(error) from error
    logger.info("VK user %s full name updated", vk_user_id)
    return user
