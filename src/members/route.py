from typing import Optional, List
from fastapi import APIRouter, Depends, Query

from src.members.schemas import (
    MemberListResponse,
    MemberDetailResponse,
    MemberSeedResponse,
)
from src.members.service import MemberService
from src.members.http_exceptions import MemberNotFound, MemberFetchError
from src.members.exceptions import MemberNotFoundError, MemberFetchError as DomainFetchError
from src.dependencies import get_member_service
from src.logging_config import create_logger

router = APIRouter()
logger = create_logger("members", __name__)


@router.get("/", response_model=MemberListResponse)
async def get_members(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    generation: Optional[str] = Query(None, description="Filter by generation (e.g., '3', '7', '11')"),
    search: Optional[str] = Query(None, description="Search by name or nickname"),
    service: MemberService = Depends(get_member_service),
):
    """
    Get all JKT48 members with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return (max 100)
    - **generation**: Filter by generation number
    - **search**: Search by member name or nickname
    """
    try:
        return await service.get_all_members(skip, limit, generation, search)
    except DomainFetchError:
        raise MemberFetchError()


@router.get("/generations", response_model=List[str])
async def get_generations(
    service: MemberService = Depends(get_member_service),
):
    """
    Get list of all available generations.
    """
    try:
        return await service.get_generations()
    except DomainFetchError:
        raise MemberFetchError()


@router.get("/id/{member_id}", response_model=MemberDetailResponse)
async def get_member_by_id(
    member_id: int,
    service: MemberService = Depends(get_member_service),
):
    """
    Get a specific JKT48 member by their ID.
    """
    try:
        return await service.get_member_by_id(member_id)
    except MemberNotFoundError:
        raise MemberNotFound()
    except DomainFetchError:
        raise MemberFetchError()


@router.get("/nickname/{nickname}", response_model=MemberDetailResponse)
async def get_member_by_nickname(
    nickname: str,
    service: MemberService = Depends(get_member_service),
):
    """
    Get a specific JKT48 member by their nickname.
    """
    try:
        return await service.get_member_by_nickname(nickname)
    except MemberNotFoundError:
        raise MemberNotFound()
    except DomainFetchError:
        raise MemberFetchError()


@router.post("/seed", response_model=MemberSeedResponse, status_code=201)
async def seed_members(
    service: MemberService = Depends(get_member_service),
):
    """
    Seed the database with JKT48 member data.
    This will clear existing data and insert fresh data.
    """
    try:
        return await service.seed_members()
    except DomainFetchError:
        raise MemberFetchError()
