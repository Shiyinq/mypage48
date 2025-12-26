from typing import List

from fastapi import APIRouter, Depends, status

from src.dependencies import get_current_user, get_theater_service
from src.auth.schemas import UserCurrent
from src.theater.service import TheaterService
from src.theater.schemas import (
    TicketCreateRequest,
    TicketResponse,
    TicketUpdateRequest,
)
from src.theater.constants import Info

router = APIRouter()


@router.post("/tickets", status_code=status.HTTP_201_CREATED, response_model=TicketResponse, response_model_by_alias=True)
async def create_ticket(
    ticket_data: TicketCreateRequest,
    current_user: UserCurrent = Depends(get_current_user),
    service: TheaterService = Depends(get_theater_service),
):
    """
    Create a new ticket.
    """
    return await service.create_ticket(current_user.userId, ticket_data)


@router.get("/tickets", response_model=List[TicketResponse], response_model_by_alias=True)
async def get_my_tickets(
    current_user: UserCurrent = Depends(get_current_user),
    service: TheaterService = Depends(get_theater_service),
):
    """
    Get all tickets for the current user.
    """
    return await service.get_my_tickets(current_user.userId)


@router.get("/tickets/{ticket_id}", response_model=TicketResponse, response_model_by_alias=True)
async def get_ticket(
    ticket_id: str,
    current_user: UserCurrent = Depends(get_current_user),
    service: TheaterService = Depends(get_theater_service),
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
    service: TheaterService = Depends(get_theater_service),
):
    """
    Update a ticket.
    """
    return await service.update_ticket(current_user.userId, ticket_id, ticket_data)


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: str,
    current_user: UserCurrent = Depends(get_current_user),
    service: TheaterService = Depends(get_theater_service),
):
    """
    Delete a ticket.
    """
    await service.delete_ticket(current_user.userId, ticket_id)
