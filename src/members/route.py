from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from src.dependencies import get_member_service, require_admin, require_csrf_protection
from src.logging_config import create_logger
from src.members.schemas import (
    BirthdayResponse,
    MemberCreateRequest,
    MemberDetailResponse,
    MemberListResponse,
    MemberResponse,
    MemberUpdateRequest,
    MessageResponse,
)
from src.members.service import MemberService

router = APIRouter()
logger = create_logger("members", __name__)


@router.get("", response_model=MemberListResponse)
async def get_members(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    generation: Optional[str] = Query(
        None, description="Filter by generation (e.g., '3', '7', '11')"
    ),
    search: Optional[str] = Query(None, description="Search by name or nickname"),
    include_inactive: bool = Query(False, description="Include inactive/ex-members"),
    service: MemberService = Depends(get_member_service),
):
    """
    Get all JKT48 members with optional filtering.

    - **page**: Page number (default 1)
    - **limit**: Items per page (default 20, max 100)
    - **generation**: Filter by generation number
    - **search**: Search by member name or nickname
    - **include_inactive**: Include inactive/ex-members (default False)
    """
    return await service.get_all_members(
        page, limit, generation, search, include_inactive
    )


@router.get("/generations", response_model=List[str])
async def get_generations(
    service: MemberService = Depends(get_member_service),
):
    """
    Get list of all available generations.
    """
    return await service.get_generations()


@router.get("/birthdays", response_model=List[BirthdayResponse])
async def get_upcoming_birthdays(
    service: MemberService = Depends(get_member_service),
):
    """
    Get members with upcoming birthdays in the next 30 days.
    """
    return await service.get_upcoming_birthdays()


@router.get("/id/{member_id}", response_model=MemberDetailResponse)
async def get_member_by_id(
    member_id: str,
    service: MemberService = Depends(get_member_service),
):
    """
    Get a specific JKT48 member by their ID.
    """
    return await service.get_member_by_id(member_id)


@router.get("/nickname/{nickname}", response_model=MemberDetailResponse)
async def get_member_by_nickname(
    nickname: str,
    service: MemberService = Depends(get_member_service),
):
    """
    Get a specific JKT48 member by their nickname.
    """
    return await service.get_member_by_nickname(nickname)


# ============ Admin-only CRUD endpoints ============


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=MemberResponse,
    dependencies=[Depends(require_admin), Depends(require_csrf_protection)],
)
async def create_member(
    data: MemberCreateRequest,
    service: MemberService = Depends(get_member_service),
):
    """
    Create a new member. **Admin only.**
    """
    return await service.create_member(data)


@router.put(
    "/{member_id}",
    response_model=MemberResponse,
    dependencies=[Depends(require_admin), Depends(require_csrf_protection)],
)
async def update_member(
    member_id: str,
    data: MemberUpdateRequest,
    service: MemberService = Depends(get_member_service),
):
    """
    Update a member by ID. **Admin only.**
    """
    return await service.update_member(member_id, data)


@router.delete(
    "/{member_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin), Depends(require_csrf_protection)],
)
async def delete_member(
    member_id: str,
    service: MemberService = Depends(get_member_service),
):
    """
    Delete a member by ID. **Admin only.**
    """
    return await service.delete_member(member_id)
