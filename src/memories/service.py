from typing import Optional

from src.config import Settings
from src.logging_config import create_logger
from src.memories.exceptions import MemoriesFetchError
from src.memories.repository import MemoriesRepository
from src.memories.schemas import (
    MemoryItem,
    MemoryType,
    MemoriesPaginationResponse,
)
from src.tickets.schemas import PaginationMeta

logger = create_logger("memories_service", __name__)


class MemoriesService:
    def __init__(
        self,
        repository: MemoriesRepository,
        config: Settings,
    ):
        self.repository = repository
        self.config = config

    async def get_memories_paginated(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        type_filter: Optional[str] = None,
    ) -> MemoriesPaginationResponse:
        """
        Get paginated memories for a user.
        
        Args:
            user_id: User's ID
            page: Page number (1-indexed)
            limit: Items per page (max 100)
            type_filter: 'TICKET', '2SHOT', or None for all
            
        Returns:
            MemoriesPaginationResponse with data and pagination meta
        """
        try:
            # Enforce limits
            if limit > 100:
                limit = 100
            if page < 1:
                page = 1

            items_data, total_count = await self.repository.get_memories_paginated(
                user_id=user_id,
                page=page,
                limit=limit,
                type_filter=type_filter,
            )

            # Transform raw data to MemoryItem models
            memory_items = []
            for item in items_data:
                # Build subtitle based on type
                if item["type"] == "TICKET":
                    subtitle = f"{item.get('seatSection', '')}-{item.get('seatNumber', '')}"
                else:
                    subtitle = item.get("twoShotType", "Roulette")

                memory_items.append(
                    MemoryItem(
                        uniqueId=f"{item['ticketId']}-{item['type'].lower()}",
                        type=MemoryType(item["type"]),
                        imageUrl=item["imageUrl"],
                        date=item["date"],
                        time=item["time"],
                        title=item["title"],
                        subtitle=subtitle,
                        notes=item.get("notes"),
                        eventTitle=item.get("eventTitle"),
                        twoShotMemberName=item.get("twoShotMemberName"),
                    )
                )

            # Calculate pagination meta
            last_page = (total_count + limit - 1) // limit if limit > 0 else 1
            if last_page < 1:
                last_page = 1
            next_page = page + 1 if page < last_page else None

            return MemoriesPaginationResponse(
                data=memory_items,
                meta=PaginationMeta(
                    current_page=page,
                    last_page=last_page,
                    total_data=total_count,
                    per_page=limit,
                    next_page=next_page,
                ),
            )

        except Exception as e:
            logger.exception(f"Error fetching memories: {str(e)}")
            raise MemoriesFetchError()
