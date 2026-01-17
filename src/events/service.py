from datetime import datetime, timedelta
from math import ceil
from typing import List
import calendar

from src.config import Settings
from src.interfaces import BackgroundTaskRunner
from src.logging_config import create_logger
from src.events.repository import EventsRepository
from src.events.schemas import Event, EventPaginationResponse, PaginationMeta, CalendarEvent
from src.events.exceptions import EventFetchError

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

        try:
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
        except Exception as e:
            logger.exception(f"Failed to fetch paginated events: {str(e)}")
            raise EventFetchError() from e

    async def get_calendar_events(self, year: int, month: int) -> List[CalendarEvent]:
        # 1. Start Date (Start of the week containing the 1st)
        # We assume Sunday as the start of the week.
        first_of_month = datetime(year, month, 1)
        # weekday(): Mon=0, ..., Sat=5, Sun=6
        # padding needed for Sunday start: (weekday + 1) % 7
        days_to_subtract = (first_of_month.weekday() + 1) % 7
        start_date = first_of_month - timedelta(days=days_to_subtract)
        # Ensure time is 00:00:00
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 2. End Date (Fixed 42 days / 6 weeks from start)
        # The frontend renders a fixed 6-row grid (7 cols * 6 rows = 42 days).
        # We need to fetch enough data to cover this entire grid, including "overflow" into next month.
        end_date = start_date + timedelta(days=42)
        # Ensure time is 23:59:59 (technically end_date is exclusive in range math usually, but $lte uses inclusive)
        # Let's subtract a microsecond to be safe if we treat it as bound, or just set to end of day.
        # Here we set exactly 42 days later.
        end_date = end_date - timedelta(microseconds=1)
        
        try:
            raw_events = await self.repository.find_events_by_date_range(start_date, end_date)
            return [CalendarEvent(**e) for e in raw_events]
        except Exception as e:
            logger.exception(f"Failed to fetch calendar events: {str(e)}")
            raise EventFetchError() from e
