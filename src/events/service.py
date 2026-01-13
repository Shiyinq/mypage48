from datetime import datetime
from math import ceil
from typing import List

from src.config import Settings
from src.interfaces import BackgroundTaskRunner
from src.logging_config import create_logger
from src.events.repository import EventsRepository
from src.events.schemas import Event, EventPaginationResponse, PaginationMeta

logger = create_logger("events_service", __name__)

class EventsService:
    def __init__(
        self,
        repository: EventsRepository,
        background_tasks: BackgroundTaskRunner,
        config: Settings,
    ):
        self.repository = repository
        self.background_tasks = background_tasks
        self.config = config

    async def get_events_paginated(
        self, page: int = 1, limit: int = 20, current_only: bool = False
    ) -> EventPaginationResponse:
        query = {}
        if current_only:
            now = datetime.now()
            # Assuming 'date' is stored as datetime or ISO string that compares correctly
            # Based on user input: "date": "2026-02-07T00:00:00" which matches datetime
            query["date"] = {"$gte": now}

        total_data = await self.repository.count_events(query)
        last_page = ceil(total_data / limit) if limit > 0 else 1
        
        # Ensure page is within bounds
        if page < 1:
            page = 1
        
        skip = (page - 1) * limit
        
        sort_direction = 1 if current_only else -1
        raw_events = await self.repository.find_events_paginated(skip, limit, query, sort_direction)
        
        events_data = [Event(**e) for e in raw_events]
        
        next_page = page + 1 if page < last_page else None
        
        meta = PaginationMeta(
            current_page=page,
            last_page=last_page,
            total_data=total_data,
            per_page=limit,
            next_page=next_page,
        )
        
        return EventPaginationResponse(data=events_data, meta=meta)
