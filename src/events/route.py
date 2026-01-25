from typing import List

from fastapi import APIRouter, Depends, Query

from src.auth.schemas import UserCurrent
from src.dependencies import get_current_user, get_events_service
from src.events.schemas import CalendarEvent, EventPaginationResponse
from src.events.service import EventsService

router = APIRouter()


@router.get("/", response_model=EventPaginationResponse)
async def get_events(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: EventsService = Depends(get_events_service),
    _current_user: UserCurrent = Depends(get_current_user),
):
    """
    Get all events with pagination.
    """
    return await service.get_events_paginated(page=page, limit=limit)


@router.get("/current", response_model=EventPaginationResponse)
async def get_current_events(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: EventsService = Depends(get_events_service),
    _current_user: UserCurrent = Depends(get_current_user),
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
    _current_user: UserCurrent = Depends(get_current_user),
):
    """
    Get events for a specific month and year.
    Returns a light version of events optimized for calendar view.
    """
    return await service.get_calendar_events(year=year, month=month)
