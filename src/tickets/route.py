from typing import List

from fastapi import APIRouter, Depends, Query, status

from src.auth.schemas import UserCurrent
from src.dependencies import (
    get_current_user,
    get_tickets_service,
    require_csrf_protection,
)
from src.tickets.schemas import (
    MessageResponse,
    TicketCreateRequest,
    TicketPaginationResponse,
    TicketResponse,
    TicketUpdateRequest,
)
from src.tickets.service import TicketsService

router = APIRouter()


@router.post(
    "/tickets",
    status_code=status.HTTP_201_CREATED,
    response_model=TicketResponse,
    response_model_by_alias=True,
)
async def create_ticket(
    ticket_data: TicketCreateRequest,
    current_user: UserCurrent = Depends(get_current_user),
    service: TicketsService = Depends(get_tickets_service),
    _=Depends(require_csrf_protection),
):
    """
    Create a new ticket.
    """
    return await service.create_ticket(current_user.userId, ticket_data)


@router.get(
    "/tickets", response_model=TicketPaginationResponse, response_model_by_alias=True
)
async def get_my_tickets(
    page: int = 1,
    limit: int = 20,
    title: str | None = None,
    has_two_shot: bool | None = None,
    is_favorite: bool | None = None,
    # FastAPI handles list query params as ?days=Sat&days=Sun
    days: List[str] | None = Query(default=None),
    start_date: str | None = None,
    end_date: str | None = None,
    current_user: UserCurrent = Depends(get_current_user),
    service: TicketsService = Depends(get_tickets_service),
):
    """
    Get all tickets for the current user with advanced filtering options.

    Args:
        page (int): Page number for pagination (default: 1)
        limit (int): Number of items per page (default: 20)
        title (str | None): Filter by setlist title (partial match supported)
        has_two_shot (bool | None): If True, only return tickets with 2-shot content
        days (List[str] | None): Filter by days of the week (e.g. ["Saturday", "Sunday"])
        start_date (str | None): Filter by start date (YYYY-MM-DD)
        end_date (str | None): Filter by end date (YYYY-MM-DD)

    Returns:
        TicketPaginationResponse: Paginated list of tickets matching the filters
    """
    return await service.get_tickets_paginated(
        current_user.userId,
        page=page,
        limit=limit,
        title=title,
        has_two_shot=has_two_shot,
        is_favorite=is_favorite,
        days=days,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/tickets/titles", response_model=List[str])
async def get_ticket_titles(
    current_user: UserCurrent = Depends(get_current_user),
    service: TicketsService = Depends(get_tickets_service),
):
    """
    Get distinct ticket titles for the current user.
    """
    return await service.get_ticket_titles(current_user.userId)


@router.get(
    "/tickets/{ticket_id}", response_model=TicketResponse, response_model_by_alias=True
)
async def get_ticket(
    ticket_id: str,
    current_user: UserCurrent = Depends(get_current_user),
    service: TicketsService = Depends(get_tickets_service),
):
    """
    Get a specific ticket by ID.
    """
    return await service.get_ticket(current_user.userId, ticket_id)


@router.patch(
    "/tickets/{ticket_id}/favorite",
    response_model=TicketResponse,
    response_model_by_alias=True,
)
async def toggle_ticket_favorite(
    ticket_id: str,
    current_user: UserCurrent = Depends(get_current_user),
    service: TicketsService = Depends(get_tickets_service),
    _=Depends(require_csrf_protection),
):
    """
    Toggle the favorite status of a ticket.
    """
    return await service.toggle_favorite(current_user.userId, ticket_id)


@router.put(
    "/tickets/{ticket_id}", response_model=TicketResponse, response_model_by_alias=True
)
async def update_ticket(
    ticket_id: str,
    ticket_data: TicketUpdateRequest,
    current_user: UserCurrent = Depends(get_current_user),
    service: TicketsService = Depends(get_tickets_service),
    _=Depends(require_csrf_protection),
):
    """
    Update a ticket.
    """
    return await service.update_ticket(current_user.userId, ticket_id, ticket_data)


@router.delete(
    "/tickets/{ticket_id}",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
async def delete_ticket(
    ticket_id: str,
    current_user: UserCurrent = Depends(get_current_user),
    service: TicketsService = Depends(get_tickets_service),
    _=Depends(require_csrf_protection),
):
    """
    Delete a ticket.
    """
    return await service.delete_ticket(current_user.userId, ticket_id)
