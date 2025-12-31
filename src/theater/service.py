from datetime import datetime, timezone
from typing import List, Optional

from src.config import Settings
from src.infrastructure import AsyncBackgroundRunner
from src.logging_config import create_logger
from src.theater.repository import TheaterRepository
from src.theater.schemas import (
    TicketCreateRequest,
    TicketInDB,
    TicketResponse,

    TicketUpdateRequest,
    MessageResponse,
)
from src.theater.constants import Info
from src.theater.exceptions import (
    TicketCreationError,
    TicketNotFoundError,
    TicketUpdateError,
    TicketDeletionError
)

logger = create_logger("theater_service", __name__)


class TheaterService:
    def __init__(
        self,
        repository: TheaterRepository,
        background_tasks: AsyncBackgroundRunner,
        config: Settings,
    ):
        self.repository = repository
        self.background_tasks = background_tasks
        self.config = config

    async def create_ticket(self, user_id: str, data: TicketCreateRequest) -> TicketResponse:
        try:
            now = datetime.now(timezone.utc)
            ticket_in_db = TicketInDB(
                **data.model_dump(),
                user_id=user_id,
                created_at=now,
                updated_at=now
            )
            result = await self.repository.create_ticket(ticket_in_db)
            
            # Map _id manually for response
            ticket_dict = ticket_in_db.model_dump()
            ticket_dict["_id"] = str(result.inserted_id)
            
            return TicketResponse(**ticket_dict)
        except Exception as e:
            logger.exception(f"Error creating ticket: {str(e)}")
            raise TicketCreationError()

    async def get_my_tickets(self, user_id: str) -> List[TicketResponse]:
        tickets = await self.repository.get_all_tickets(user_id)
        results = []
        for t in tickets:
            t["_id"] = str(t["_id"])
            results.append(TicketResponse(**t))
        return results

    async def get_ticket(self, user_id: str, ticket_id: str) -> TicketResponse:
        ticket = await self.repository.get_ticket(ticket_id, user_id)
        if not ticket:
            raise TicketNotFoundError()
        ticket["_id"] = str(ticket["_id"])
        return TicketResponse(**ticket)

    async def update_ticket(
        self, user_id: str, ticket_id: str, data: TicketUpdateRequest
    ) -> TicketResponse:
        try:
            updated_ticket = await self.repository.update_ticket(ticket_id, user_id, data)
            if not updated_ticket:
                raise TicketNotFoundError()
            updated_ticket["_id"] = str(updated_ticket["_id"])
            return TicketResponse(**updated_ticket)
        except TicketNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error updating ticket: {str(e)}")
            raise TicketUpdateError()

    async def delete_ticket(self, user_id: str, ticket_id: str) -> MessageResponse:
        try:
            success = await self.repository.delete_ticket(ticket_id, user_id)
            if not success:
                raise TicketNotFoundError()
            return MessageResponse(detail=Info.TICKET_DELETED)
        except TicketNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error deleting ticket: {str(e)}")
            raise TicketDeletionError()
