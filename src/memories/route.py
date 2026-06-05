from typing import Optional

from fastapi import APIRouter, Depends

from src.auth.schemas import UserCurrent
from src.dependencies import get_current_user, get_memories_service
from src.memories.schemas import MemoriesPaginationResponse, TopTwoShotResponse
from src.memories.service import MemoriesService

router = APIRouter()


@router.get("", response_model=MemoriesPaginationResponse)
async def get_memories(
    page: int = 1,
    limit: int = 20,
    type: Optional[str] = None,
    title: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    days: Optional[str] = None,
    current_user: UserCurrent = Depends(get_current_user),
    memories_service: MemoriesService = Depends(get_memories_service),
):
    """
    Get paginated memory items (ticket and 2-shot images).

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 20, max: 100)
        type: Filter by type ('TICKET', '2SHOT', or omit for all)

    Returns:
        MemoriesPaginationResponse: Paginated list of memory items
    """
    return await memories_service.get_memories_paginated(
        user_id=current_user.userId,
        page=page,
        limit=limit,
        type_filter=type,
        title=title,
        start_date=start_date,
        end_date=end_date,
        days=days.split(",") if days else None,
    )


@router.get("/top-two-shot", response_model=TopTwoShotResponse)
async def get_top_two_shot(
    current_user: UserCurrent = Depends(get_current_user),
    memories_service: MemoriesService = Depends(get_memories_service),
):
    """
    Get Top 2-Shot statistics.
    """
    return await memories_service.get_top_two_shot(user_id=current_user.userId)
