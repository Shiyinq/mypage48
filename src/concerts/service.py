from typing import List

from src.concerts.constants import Info
from src.concerts.exceptions import (
    ConcertCreationError,
    ConcertDeleteError,
    ConcertNotFoundError,
    ConcertUpdateError,
)
from src.concerts.repository import ConcertsRepository
from src.concerts.schemas import ConcertResponse, CreateConcert, UpdateConcert
from src.config import Settings
from src.interfaces import BackgroundTaskRunner
from src.logging_config import create_logger

logger = create_logger("concerts_service", __name__)


class ConcertsService:
    def __init__(
        self,
        repository: ConcertsRepository,
        background_tasks: BackgroundTaskRunner,
        config: Settings,
    ):
        self.repository = repository
        self.background_tasks = background_tasks
        self.config = config

    def _map_to_response(self, item: dict) -> ConcertResponse:
        item["id"] = str(item.pop("_id"))
        return ConcertResponse(**item)

    async def create_concert(self, data: CreateConcert) -> ConcertResponse:
        try:
            result = await self.repository.insert_concert(data)
            concert = await self.repository.find_concert_by_id(str(result.inserted_id))
            return self._map_to_response(concert)
        except Exception as e:
            logger.exception(f"Error creating concert: {str(e)}")
            raise ConcertCreationError()

    async def get_all_concerts(self) -> List[ConcertResponse]:
        items = await self.repository.get_all_concerts()
        return [self._map_to_response(item) for item in items]

    async def get_concert(self, concert_id: str) -> ConcertResponse:
        item = await self.repository.find_concert_by_id(concert_id)
        if not item:
            raise ConcertNotFoundError()
        return self._map_to_response(item)

    async def update_concert(
        self, concert_id: str, data: UpdateConcert
    ) -> ConcertResponse:
        # Check if exists
        await self.get_concert(concert_id)

        success = await self.repository.update_concert(concert_id, data)
        if not success:
            raise ConcertUpdateError()

        updated_item = await self.repository.find_concert_by_id(concert_id)
        return self._map_to_response(updated_item)

    async def delete_concert(self, concert_id: str) -> dict:
        # Check if exists
        await self.get_concert(concert_id)

        success = await self.repository.delete_concert(concert_id)
        if not success:
            raise ConcertDeleteError()

        return {"detail": Info.CONCERT_DELETED}
