from fastapi import APIRouter, Depends, Query
from src.dependencies import get_events_service
from src.events.schemas import EventPaginationResponse
from src.events.service import EventsService

router = APIRouter()


@router.get("/", response_model=EventPaginationResponse)
async def get_events(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: EventsService = Depends(get_events_service),
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
):
    """
    Get current and future events with pagination.
    """
    return await service.get_events_paginated(page=page, limit=limit, current_only=True)
