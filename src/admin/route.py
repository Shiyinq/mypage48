from fastapi import APIRouter, Depends, Query

from src.admin.schemas import DataMyPageStats, DataTheaterStats, DataUsersStats
from src.admin.service import AdminService
from src.dependencies import get_admin_service, require_admin

router = APIRouter()


@router.get("/dashboard/users", response_model=DataUsersStats)
async def get_users_stats(
    active_days: int = Query(7, description="Number of days to consider a user active"),
    _=Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    return await service.get_users_stats(active_days)


@router.get("/dashboard/mypage", response_model=DataMyPageStats)
async def get_mypage_stats(
    _=Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    return await service.get_mypage_stats()


@router.get("/dashboard/theater", response_model=DataTheaterStats)
async def get_theater_stats(
    _=Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    return await service.get_theater_stats()
