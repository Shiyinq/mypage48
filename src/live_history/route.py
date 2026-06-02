from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from src.auth.schemas import UserCurrent
from src.dependencies import get_current_user, get_live_history_service
from src.live_history.exceptions import LiveHistoryUpdateError
from src.live_history.http_exceptions import LiveHistoryUpdateFailed
from src.live_history.schemas import (
    LiveHistoryPaginationResponse,
    LiveHistoryStatsResponse,
    LiveHistoryUpdateRequest,
    MemberLiveHistoryStatsResponse,
)
from src.live_history.service import LiveHistoryService

router = APIRouter()


@router.post("/update", status_code=status.HTTP_204_NO_CONTENT)
async def update_watch_duration(
    data: LiveHistoryUpdateRequest,
    current_user: UserCurrent = Depends(get_current_user),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    try:
        await service.update_watch_duration(user_id=current_user.userId, data=data)
    except LiveHistoryUpdateError:
        raise LiveHistoryUpdateFailed()


@router.get("/watched", response_model=LiveHistoryPaginationResponse)
async def get_live_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    member_id: Optional[str] = Query(None),
    current_user: UserCurrent = Depends(get_current_user),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    return await service.get_user_history(
        user_id=current_user.userId, page=page, limit=limit, member_id=member_id
    )


@router.get("/watched/stats", response_model=LiveHistoryStatsResponse)
async def get_overall_stats(
    current_user: UserCurrent = Depends(get_current_user),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    return await service.get_overall_stats(user_id=current_user.userId)


@router.get(
    "/watched/members/{member_id}/stats", response_model=MemberLiveHistoryStatsResponse
)
async def get_member_stats(
    member_id: str,
    current_user: UserCurrent = Depends(get_current_user),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    return await service.get_member_stats(
        user_id=current_user.userId, member_id=member_id
    )
