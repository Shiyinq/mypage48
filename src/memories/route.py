from typing import Optional

from fastapi import APIRouter, Depends

from src import dependencies
from src.auth.schemas import UserCurrent
from src.dependencies import get_memories_service, get_storage_service
from src.memories.schemas import MemoriesPaginationResponse, TopTwoShotResponse
from src.memories.service import MemoriesService
from src.storage.service import StorageService

router = APIRouter()


@router.get("", response_model=MemoriesPaginationResponse)
async def get_memories(
    page: int = 1,
    limit: int = 20,
    type: Optional[str] = None,
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    memories_service: MemoriesService = Depends(get_memories_service),
    storage_service: StorageService = Depends(get_storage_service),
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
    result = await memories_service.get_memories_paginated(
        user_id=current_user.userId,
        page=page,
        limit=limit,
        type_filter=type,
    )

    # Resolve image URLs for all memory items
    resolved_data = [
        storage_service.resolve_memory_item_image(item) for item in result.data
    ]
    result.data = resolved_data

    return result


@router.get("/top-two-shot", response_model=TopTwoShotResponse)
async def get_top_two_shot(
    current_user: UserCurrent = Depends(dependencies.get_current_user),
    memories_service: MemoriesService = Depends(get_memories_service),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Get Top 2-Shot statistics.
    """
    stats = await memories_service.get_top_two_shot(user_id=current_user.userId)
    return storage_service.resolve_top_twoshot_images(stats)
