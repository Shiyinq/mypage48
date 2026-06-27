from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from src.dependencies import get_events_service
from src.events.schemas import (
    CalendarEvent,
    EventDetail,
    EventPaginationResponse,
    MemberEventStats,
)
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


@router.get("/member/{member_id}/stats", response_model=MemberEventStats)
async def get_member_event_stats(
    member_id: str,
    service: EventsService = Depends(get_events_service),
):
    """Get show statistics (total, top setlist, unique) for a member."""
    return await service.get_member_event_stats(member_id)


@router.get("/member/{member_id}", response_model=EventPaginationResponse)
async def get_member_events(
    member_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: EventsService = Depends(get_events_service),
):
    """
    Get all past and upcoming events for a specific member with pagination.
    """
    return await service.get_member_events_paginated(member_id, page=page, limit=limit)


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


@router.get("/{event_id}", response_model=EventDetail)
async def get_event(
    event_id: str,
    service: EventsService = Depends(get_events_service),
):
    """Get single event detail by ID."""
    event = await service.get_event_by_id(event_id)
    return event
