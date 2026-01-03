from typing import List

from fastapi import APIRouter, Depends, status

from src.dependencies import get_current_user, get_tickets_service
from src.auth.schemas import UserCurrent
from src.tickets.service import TicketsService
from src.tickets.schemas import (
    MessageResponse,
    TicketCreateRequest,
    TicketResponse,
    TicketUpdateRequest,
    TicketPaginationResponse,
)


router = APIRouter()


@router.post("/tickets", status_code=status.HTTP_201_CREATED, response_model=TicketResponse, response_model_by_alias=True)
async def create_ticket(
    ticket_data: TicketCreateRequest,
    current_user: UserCurrent = Depends(get_current_user),
    service: TicketsService = Depends(get_tickets_service),
):
    """
    Create a new ticket.
    """
    return await service.create_ticket(current_user.userId, ticket_data)


@router.get("/tickets", response_model=TicketPaginationResponse, response_model_by_alias=True)
async def get_my_tickets(
    page: int = 1,
    limit: int = 20,
    current_user: UserCurrent = Depends(get_current_user),
    service: TicketsService = Depends(get_tickets_service),
):
    """
    Get all tickets for the current user.
    """
    return await service.get_tickets_paginated(current_user.userId, page=page, limit=limit)


@router.get("/tickets/{ticket_id}", response_model=TicketResponse, response_model_by_alias=True)
async def get_ticket(
    ticket_id: str,
    current_user: UserCurrent = Depends(get_current_user),
    service: TicketsService = Depends(get_tickets_service),
):
    """
    Get a specific ticket by ID.
    """
    return await service.get_ticket(current_user.userId, ticket_id)


@router.put("/tickets/{ticket_id}", response_model=TicketResponse, response_model_by_alias=True)
async def update_ticket(
    ticket_id: str,
    ticket_data: TicketUpdateRequest,
    current_user: UserCurrent = Depends(get_current_user),
    service: TicketsService = Depends(get_tickets_service),
):
    """
    Update a ticket.
    """
    return await service.update_ticket(current_user.userId, ticket_id, ticket_data)


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_200_OK, response_model=MessageResponse)
async def delete_ticket(
    ticket_id: str,
    current_user: UserCurrent = Depends(get_current_user),
    service: TicketsService = Depends(get_tickets_service),
):
    """
    Delete a ticket.
    """
    return await service.delete_ticket(current_user.userId, ticket_id)

