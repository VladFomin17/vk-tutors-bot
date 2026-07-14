from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services import analytics
from app.services.auth import require_admin

router = APIRouter(tags=["analytics"], dependencies=[Depends(require_admin)])


class StudentResponse(BaseModel):
    id: str
    chat_id: int
    vk_user_id: int
    first_name: str
    last_name: str
    is_active: bool
    first_seen_at: datetime
    last_seen_at: datetime
    study_group_id: int
    study_group_name: str
    chat_title: str | None


class StatisticsOverview(BaseModel):
    total_groups: int
    total_students: int
    active_broadcasts: int
    completed_broadcasts: int
    responses_today: int


class DailyResponseCount(BaseModel):
    date: date
    count: int


class BroadcastCompletion(BaseModel):
    id: int
    title: str
    deadline: datetime
    recipient_count: int
    response_count: int


class GroupActivity(BaseModel):
    id: int
    name: str
    student_count: int
    recipient_count: int
    response_count: int


class StatisticsResponse(BaseModel):
    overview: StatisticsOverview
    responses_over_time: list[DailyResponseCount]
    broadcast_completion: list[BroadcastCompletion]
    group_activity: list[GroupActivity]


@router.get("/students", response_model=list[StudentResponse])
async def get_students() -> list[dict[str, object]]:
    return await analytics.list_students()


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics() -> dict[str, object]:
    return await analytics.get_statistics()
