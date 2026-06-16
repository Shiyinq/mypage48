from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from src.auth.schemas import UserCurrent
from src.dependencies import (
    get_current_user,
    get_setlists_service,
    require_admin,
    require_csrf_protection,
)
from src.logging_config import create_logger
from src.setlists.schemas import (
    MessageResponse,
    SetlistCreateRequest,
    SetlistDetailResponse,
    SetlistListResponse,
    SetlistResponse,
    SetlistUpdateRequest,
)
from src.setlists.service import SetlistsService

router = APIRouter()
logger = create_logger("setlists", __name__)


@router.get("", response_model=SetlistListResponse)
async def get_setlists(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=100, description="Maximum number of records to return"
    ),
    type: Optional[str] = Query(None, description="Filter by type (setlist, event)"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(
        None, description="Search by title or Japanese title"
    ),
    year: Optional[int] = Query(None, description="Filter by year"),
    startMonth: Optional[int] = Query(None, description="Filter by start month (0-11)"),
    endMonth: Optional[int] = Query(None, description="Filter by end month (0-11)"),
    isAllData: bool = Query(
        False, description="Whether to include all data ignoring date filters"
    ),
    service: SetlistsService = Depends(get_setlists_service),
    current_user: UserCurrent = Depends(get_current_user),
):
    """
    Get all JKT48 theater setlists with optional filtering.
    Includes user-specific ticket statistics (count, percentage, isMostWatched).

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (max 100)
    - **type**: Filter by setlist type (setlist or event)
    - **active**: Filter by active status
    """
    return await service.get_all_setlists(
        current_user.userId,
        skip,
        limit,
        type,
        active,
        search,
        year=year,
        start_month=startMonth,
        end_month=endMonth,
        is_all_data=isAllData,
    )


@router.get("/types", response_model=List[str])
async def get_types(
    service: SetlistsService = Depends(get_setlists_service),
    _current_user: UserCurrent = Depends(get_current_user),
):
    """
    Get list of all available setlist types.
    """
    return await service.get_types()


@router.get("/id/{setlist_id}", response_model=SetlistResponse)
async def get_setlist_by_id(
    setlist_id: str,
    service: SetlistsService = Depends(get_setlists_service),
    _current_user: UserCurrent = Depends(get_current_user),
):
    """
    Get a specific setlist by its ID.
    """
    return await service.get_setlist_by_id(setlist_id)


@router.get("/detail/{setlist_id}", response_model=SetlistDetailResponse)
async def get_setlist_detail(
    setlist_id: str,
    year: Optional[int] = Query(None, description="Filter by year"),
    startMonth: Optional[int] = Query(None, description="Filter by start month (0-11)"),
    endMonth: Optional[int] = Query(None, description="Filter by end month (0-11)"),
    isAllData: bool = Query(
        False, description="Whether to include all data ignoring date filters"
    ),
    service: SetlistsService = Depends(get_setlists_service),
    current_user: UserCurrent = Depends(get_current_user),
):
    """
    Get setlist detail with user's tickets and computed statistics.
    Includes attendance stats, spending info, and ticket history.
    """
    return await service.get_setlist_detail(
        setlist_id,
        current_user.userId,
        year=year,
        start_month=startMonth,
        end_month=endMonth,
        is_all_data=isAllData,
    )


@router.get("/title/{title}", response_model=SetlistResponse)
async def get_setlist_by_title(
    title: str,
    service: SetlistsService = Depends(get_setlists_service),
    _current_user: UserCurrent = Depends(get_current_user),
):
    """
    Get a specific setlist by its title.
    """
    return await service.get_setlist_by_title(title)


# ============ Admin-only CRUD endpoints ============


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SetlistResponse,
    dependencies=[Depends(require_admin), Depends(require_csrf_protection)],
)
async def create_setlist(
    data: SetlistCreateRequest,
    service: SetlistsService = Depends(get_setlists_service),
):
    """
    Create a new setlist. **Admin only.**
    """
    return await service.create_setlist(data)


@router.put(
    "/{setlist_id}",
    response_model=SetlistResponse,
    dependencies=[Depends(require_admin), Depends(require_csrf_protection)],
)
async def update_setlist(
    setlist_id: str,
    data: SetlistUpdateRequest,
    service: SetlistsService = Depends(get_setlists_service),
):
    """
    Update a setlist by ID. **Admin only.**
    """
    return await service.update_setlist(setlist_id, data)


@router.delete(
    "/{setlist_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin), Depends(require_csrf_protection)],
)
async def delete_setlist(
    setlist_id: str,
    service: SetlistsService = Depends(get_setlists_service),
):
    """
    Delete a setlist by ID. **Admin only.**
    """
    return await service.delete_setlist(setlist_id)
