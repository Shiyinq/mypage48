from datetime import datetime, timezone

from src.config import Settings
from src.logging_config import create_logger
from src.sorter.exceptions import SorterNotFoundError, SorterSaveError
from src.sorter.repository import SortersRepository
from src.sorter.schemas import (
    PaginationMeta,
    SorterCreateRequest,
    SorterInDB,
    SorterPaginationResponse,
    SorterResponse,
    SorterUpdateRequest,
)

logger = create_logger("sorter_service", __name__)


class SortersService:
    def __init__(self, repository: SortersRepository, config: Settings):
        self.repository = repository
        self.config = config

    async def save_sorter(
        self, user_id: str, data: SorterCreateRequest
    ) -> SorterResponse:
        try:
            now = datetime.now(timezone.utc)
            sorter_db = SorterInDB(
                user_id=user_id,
                title=data.title,
                description=data.description,
                filters=data.filters,
                results=data.results,
                created_at=now,
                updated_at=now,
            )
            result = await self.repository.create_sorter(sorter_db)
            inserted_id = str(result.inserted_id)

            created = await self.repository.get_sorter(inserted_id, user_id)
            if not created:
                raise SorterSaveError()
            return SorterResponse(**created)
        except Exception as e:
            logger.exception(f"Error saving sorter: {str(e)}")
            raise SorterSaveError()

    async def get_sorter(self, sorter_id: str, user_id: str) -> SorterResponse:
        sorter = await self.repository.get_sorter(sorter_id, user_id)
        if not sorter:
            raise SorterNotFoundError()
        return SorterResponse(**sorter)

    async def get_sorters(
        self, user_id: str, page: int = 1, limit: int = 15
    ) -> SorterPaginationResponse:
        sorters, total = await self.repository.get_sorters(user_id, page, limit)

        last_page = (total + limit - 1) // limit if limit > 0 else 1
        if last_page == 0:
            last_page = 1
        next_page = page + 1 if page < last_page else None

        return SorterPaginationResponse(
            data=[SorterResponse(**s) for s in sorters],
            meta=PaginationMeta(
                current_page=page,
                last_page=last_page,
                total_data=total,
                per_page=limit,
                next_page=next_page,
            ),
        )

    async def delete_sorter(self, sorter_id: str, user_id: str) -> bool:
        success = await self.repository.delete_sorter(sorter_id, user_id)
        if not success:
            raise SorterNotFoundError()
        return True

    async def update_sorter(
        self, sorter_id: str, user_id: str, data: SorterUpdateRequest
    ) -> SorterResponse:
        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
            success = await self.repository.update_sorter(
                sorter_id, user_id, update_data
            )
            if not success:
                raise SorterNotFoundError()

        return await self.get_sorter(sorter_id, user_id)
