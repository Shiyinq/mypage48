from typing import Optional

from src.config import Settings
from src.logging_config import create_logger
from src.memories.exceptions import MemoriesFetchError
from src.memories.repository import MemoriesRepository
from src.memories.schemas import (
    MemoriesPaginationResponse,
    MemoryItem,
    MemoryType,
    TopTwoShotMember,
    TopTwoShotResponse,
)
from src.storage.service import StorageService
from src.tickets.schemas import PaginationMeta

logger = create_logger("memories_service", __name__)


class MemoriesService:
    def __init__(
        self,
        repository: MemoriesRepository,
        config: Settings,
        storage_service: StorageService,
    ):
        self.repository = repository
        self.config = config
        self.storage_service = storage_service

    def _resolve_memory_item(self, item: MemoryItem) -> MemoryItem:
        """Resolve storage paths for a memory item."""
        if item.imageUrl:
            variants = self.storage_service.resolve_image_variants(item.imageUrl)
            item.imageUrl = variants["url"]
            item.imageUrl_medium = variants["url_medium"]
            item.imageUrl_small = variants["url_small"]

        if item.notes:
            item.notes = self.storage_service.resolve_markdown_images(item.notes)

        return item

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
                    subtitle = (
                        f"{item.get('seatSection', '')}-{item.get('seatNumber', '')}"
                    )
                else:
                    subtitle = item.get("twoShotType", "Roulette")

                memory_items.append(
                    self._resolve_memory_item(
                        MemoryItem(
                            uniqueId=f"{item['ticketId']}-{item['type'].lower()}",
                            type=MemoryType(item["type"]),
                            imageUrl=item["imageUrl"],
                            blurHash=item.get("blurHash"),
                            date=item["date"],
                            time=item["time"],
                            title=item["title"],
                            subtitle=subtitle,
                            notes=item.get("notes"),
                            eventTitle=item.get("eventTitle"),
                            twoShotMemberName=item.get("twoShotMemberName"),
                        )
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

    async def get_top_two_shot(self, user_id: str) -> TopTwoShotResponse:
        """Get top 2-shot statistics."""
        try:
            stats = await self.repository.get_top_two_shot_stats(user_id)

            # Map to response model
            ranking = []
            for item in stats.get("ranking", []):
                image_url = item.get("image")
                img_medium = None
                img_small = None
                if image_url:
                    variants = self.storage_service.resolve_image_variants(image_url)
                    image_url = variants["url"]
                    img_medium = variants["url_medium"]
                    img_small = variants["url_small"]

                ranking.append(
                    TopTwoShotMember(
                        name=item["name"],
                        count=item["count"],
                        spend=item["spend"],
                        lastDate=item["lastDate"],
                        image=image_url,
                        image_medium=img_medium,
                        image_small=img_small,
                    )
                )

            return TopTwoShotResponse(
                ranking=ranking,
                totalTwoShotSpend=stats.get("totalTwoShotSpend", 0),
                totalTwoShotCount=stats.get("totalTwoShotCount", 0),
            )

        except Exception as e:
            logger.exception(f"Error fetching top 2-shot stats: {str(e)}")
            raise MemoriesFetchError()
