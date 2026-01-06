"""Dashboard Routes - API endpoints for dashboard statistics."""
from typing import Optional

from fastapi import APIRouter, Depends, Query

from src.auth.schemas import UserCurrent
from src.dashboard.schemas import DashboardStatsResponse
from src.dashboard.service import DashboardService
from src.dependencies import get_current_user, get_dashboard_service

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    year: Optional[int] = Query(None, description="Year to filter by"),
    start_month: int = Query(0, ge=0, le=11, description="Start month (0-11)"),
    end_month: int = Query(11, ge=0, le=11, description="End month (0-11)"),
    is_all_data: bool = Query(False, description="Whether to return all data"),
    current_user: UserCurrent = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardStatsResponse:
    """
    Get dashboard statistics for the current user.

    - **year**: Year to filter tickets (defaults to current year if not provided)
    - **start_month**: Start month for filtering (0 = January, 11 = December)
    - **end_month**: End month for filtering (0 = January, 11 = December)
    - **is_all_data**: If true, returns stats for all data regardless of year/month filters
    """
    return await service.get_dashboard_stats(
        user_id=current_user.userId,
        year=year,
        start_month=start_month,
        end_month=end_month,
        is_all_data=is_all_data,
    )
