from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from src.dependencies import get_events_service
from src.events.schemas import CalendarEvent, EventPaginationResponse
from src.events.service import EventsService

router = APIRouter()


@router.get("", response_model=EventPaginationResponse)
async def get_events(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    service: EventsService = Depends(get_events_service),
):
    """
    Get all events with pagination.
    """
    return await service.get_events_paginated(
        page=page, limit=limit, start_date=start_date, end_date=end_date
    )


@router.get("/current", response_model=EventPaginationResponse)
async def get_current_events(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: EventsService = Depends(get_events_service),
):
    """
    Get current and future events with pagination.
    """
    return await service.get_events_paginated(page=page, limit=limit, current_only=True)


@router.get("/calendar", response_model=List[CalendarEvent])
async def get_calendar_events(
    year: int = Query(..., ge=2000, le=3000),
    month: int = Query(..., ge=1, le=12),
    service: EventsService = Depends(get_events_service),
):
    """
    Get events for a specific month and year.
    Returns a light version of events optimized for calendar view.
    """
    return await service.get_calendar_events(year=year, month=month)
