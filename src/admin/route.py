from fastapi import APIRouter, Depends, Query

from src.admin.schemas import (
    DataMyPageStats,
    DataTheaterStats,
    DataUsersStats,
    IDNLivePlusConfig,
    IDNLivePlusConfigResponse,
)
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


@router.get("/settings/idnliveplus", response_model=IDNLivePlusConfigResponse)
async def get_idn_live_plus_config(
    _=Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    """Get the IDN Live+ configuration from settings."""
    return await service.get_idn_live_plus_config()


@router.put("/settings/idnliveplus", response_model=IDNLivePlusConfigResponse)
async def update_idn_live_plus_config(
    config: IDNLivePlusConfig,
    _=Depends(require_admin),
    service: AdminService = Depends(get_admin_service),
):
    """Update the IDN Live+ configuration in settings."""
    return await service.update_idn_live_plus_config(config)
