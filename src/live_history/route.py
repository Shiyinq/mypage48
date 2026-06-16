from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from src.auth.schemas import UserCurrent
from src.dependencies import get_current_user, get_live_history_service
from src.live_history.exceptions import LiveHistoryUpdateError
from src.live_history.http_exceptions import LiveHistoryUpdateFailed
from src.live_history.schemas import (
    GlobalLiveHistoryPaginationResponse,
    GlobalLiveHistoryStatsResponse,
    GlobalLiveMemberRankingResponse,
    GlobalSingleMemberLiveHistoryStatsResponse,
    LiveHistoryPaginationResponse,
    LiveHistoryStatsResponse,
    LiveHistoryUpdateRequest,
    MemberLiveHistoryStatsResponse,
    PCLiveHistoryPaginationResponse,
    WatchedLiveMemberRankingResponse,
)
from src.live_history.service import LiveHistoryService

router = APIRouter()


@router.get("", response_model=GlobalLiveHistoryPaginationResponse)
async def get_global_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    """Get global live history of all members."""
    return await service.get_global_history(
        page=page, limit=limit, start_date=start_date, end_date=end_date
    )


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
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: UserCurrent = Depends(get_current_user),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    return await service.get_user_history(
        user_id=current_user.userId,
        page=page,
        limit=limit,
        member_id=member_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/watched/stats", response_model=LiveHistoryStatsResponse)
async def get_overall_stats(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: UserCurrent = Depends(get_current_user),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    return await service.get_overall_stats(
        user_id=current_user.userId, start_date=start_date, end_date=end_date
    )


@router.get(
    "/watched/members/{member_id}/stats", response_model=MemberLiveHistoryStatsResponse
)
async def get_member_stats(
    member_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: UserCurrent = Depends(get_current_user),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    return await service.get_member_stats(
        user_id=current_user.userId,
        member_id=member_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/watched/members/ranking", response_model=WatchedLiveMemberRankingResponse)
async def get_watched_live_members_ranking(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: UserCurrent = Depends(get_current_user),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    return await service.get_watched_live_members_ranking(
        user_id=current_user.userId,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/stats", response_model=GlobalLiveHistoryStatsResponse)
async def get_global_stats(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    """Get global live history statistics."""
    return await service.get_global_stats(start_date=start_date, end_date=end_date)


@router.get("/members/ranking", response_model=GlobalLiveMemberRankingResponse)
async def get_global_members_ranking(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    """Get global live members ranking by frequency."""
    return await service.get_global_members_ranking(
        page=page, limit=limit, start_date=start_date, end_date=end_date
    )


@router.get(
    "/members/{member_id}/stats",
    response_model=GlobalSingleMemberLiveHistoryStatsResponse,
)
async def get_global_member_stats(
    member_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    """Get global live history statistics for a specific member."""
    return await service.get_global_member_stats(
        member_id=member_id, start_date=start_date, end_date=end_date
    )


@router.get("/members/{member_id}", response_model=GlobalLiveHistoryPaginationResponse)
async def get_global_member_history(
    member_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    """Get global live history for a specific member."""
    return await service.get_global_member_history(
        member_id=member_id,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/pc", response_model=PCLiveHistoryPaginationResponse)
async def get_pc_collection(
    collection_type: str = Query(
        "all", description="Type of collection: owned, unowned, or all"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    sort_by: str = Query("date_desc", description="Sort by: date_desc, date_asc, tier_desc, tier_asc"),
    current_user: UserCurrent = Depends(get_current_user),
    service: LiveHistoryService = Depends(get_live_history_service),
):
    """Get PC Live Collection items marked with ownership status."""
    return await service.get_pc_collection(
        user_id=current_user.userId,
        collection_type=collection_type,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
    )
