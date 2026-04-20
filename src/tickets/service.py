from datetime import datetime, timezone
from typing import List, Optional

from src.config import Settings
from src.image_validation import ImageTooLargeError as ImageTooLargeValidationError
from src.image_validation import ImageValidationError
from src.image_validation import (
    InvalidImageTypeError as InvalidImageTypeValidationError,
)
from src.image_validation import validate_base64_image
from src.logging_config import create_logger
from src.storage.service import StorageService
from src.tickets.constants import Info
from src.tickets.exceptions import (
    ImageTooLargeError,
    InvalidImageError,
    InvalidImageTypeError,
    TicketCreationError,
    TicketDeletionError,
    TicketFetchError,
    TicketNotFoundError,
    TicketUpdateError,
)
from src.tickets.repository import TicketsRepository
from src.tickets.schemas import (
    MessageResponse,
    PaginationMeta,
    TicketCreateRequest,
    TicketInDB,
    TicketPaginationResponse,
    TicketResponse,
    TicketUpdateRequest,
)

logger = create_logger("theater_service", __name__)


class TicketsService:
    def __init__(
        self,
        repository: TicketsRepository,
        config: Settings,
        storage_service: StorageService,
    ):
        self.repository = repository
        self.config = config
        self.storage_service = storage_service

    def _resolve_ticket(self, ticket: dict) -> dict:
        """Resolve storage paths for ticket images and notes."""
        if ticket.get("imageUrl"):
            variants = self.storage_service.resolve_image_variants(ticket["imageUrl"])
            ticket["imageUrl"] = variants["url"]
            ticket["imageUrl_medium"] = variants["url_medium"]
            ticket["imageUrl_small"] = variants["url_small"]

        if ticket.get("two_shot") and ticket["two_shot"].get("imageUrl"):
            variants = self.storage_service.resolve_image_variants(
                ticket["two_shot"]["imageUrl"]
            )
            ticket["two_shot"]["imageUrl"] = variants["url"]
            ticket["two_shot"]["imageUrl_medium"] = variants["url_medium"]
            ticket["two_shot"]["imageUrl_small"] = variants["url_small"]

        if ticket.get("notes"):
            ticket["notes"] = self.storage_service.resolve_markdown_images(
                ticket.get("notes")
            )

        return ticket

    @staticmethod
    def _validate_images(
        image_url: Optional[str], two_shot_image_url: Optional[str]
    ) -> None:
        """Validate ticket and 2-shot images if provided."""
        for url in [image_url, two_shot_image_url]:
            # Only validate base64 images (legacy uploads)
            # Storage filenames skip validation
            if url and url.startswith("data:"):
                try:
                    validate_base64_image(url)
                except ImageTooLargeValidationError:
                    raise ImageTooLargeError()
                except InvalidImageTypeValidationError:
                    raise InvalidImageTypeError()
                except ImageValidationError:
                    raise InvalidImageError()

    async def create_ticket(
        self, user_id: str, data: TicketCreateRequest
    ) -> TicketResponse:
        try:
            # Validate images if provided
            two_shot_image = data.two_shot.imageUrl if data.two_shot else None
            self._validate_images(data.imageUrl, two_shot_image)

            now = datetime.now(timezone.utc)
            ticket_in_db = TicketInDB(
                **data.model_dump(), user_id=user_id, created_at=now, updated_at=now
            )
            result = await self.repository.create_ticket(ticket_in_db)

            # Map _id manually for response
            ticket_dict = ticket_in_db.model_dump()
            ticket_dict["_id"] = result.inserted_id

            return TicketResponse(**self._resolve_ticket(ticket_dict))
        except (ImageTooLargeError, InvalidImageTypeError, InvalidImageError):
            raise
        except Exception as e:
            logger.exception(f"Error creating ticket: {str(e)}")
            raise TicketCreationError()

    async def get_tickets_paginated(
        self,
        user_id: str,
        page: int,
        limit: int,
        year: Optional[int] = None,
        title: Optional[str] = None,
        has_two_shot: Optional[bool] = None,
        days: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> TicketPaginationResponse:
        try:
            # Enforce max limit of 100
            if limit > 100:
                limit = 100

            # Default pagination values if not provided (though route usually provides them)
            current_page = page if page else 1
            per_page = limit if limit else 20

            tickets_data, total_count = await self.repository.get_tickets(
                user_id,
                year,
                current_page,
                per_page,
                title=title,
                has_two_shot=has_two_shot,
                days=days,
                start_date=start_date,
                end_date=end_date,
            )

            results = []
            for t in tickets_data:
                results.append(TicketResponse(**self._resolve_ticket(t)))

            # Calculate total pages
            last_page = (total_count + per_page - 1) // per_page if per_page > 0 else 1
            if last_page < 1:
                last_page = 1

            next_page = current_page + 1 if current_page < last_page else None

            return TicketPaginationResponse(
                data=results,
                meta=PaginationMeta(
                    current_page=current_page,
                    last_page=last_page,
                    total_data=total_count,
                    per_page=per_page,
                    next_page=next_page,
                ),
            )
        except Exception:
            raise TicketFetchError()

    async def get_ticket_titles(self, user_id: str) -> List[str]:
        return await self.repository.get_distinct_titles(user_id)

    async def get_my_tickets(
        self,
        user_id: str,
        year: Optional[int] = None,
    ) -> List[TicketResponse]:
        """
        Get all tickets for internal use (stats etc).
        Returns list of tickets without pagination metadata.
        """
        try:
            # We don't pass page/limit here to get all data
            tickets_data, _ = await self.repository.get_tickets(
                user_id, year, page=None, limit=None
            )
            results = []
            for t in tickets_data:
                results.append(TicketResponse(**self._resolve_ticket(t)))
            return results
        except Exception as e:
            logger.exception(f"Error fetching tickets: {str(e)}")
            raise TicketFetchError()

    async def get_ticket(self, user_id: str, ticket_id: str) -> TicketResponse:
        try:
            ticket = await self.repository.get_ticket(ticket_id, user_id)
            if not ticket:
                raise TicketNotFoundError()
            return TicketResponse(**self._resolve_ticket(ticket))
        except TicketNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error fetching ticket: {str(e)}")
            raise TicketFetchError()

    async def update_ticket(
        self, user_id: str, ticket_id: str, data: TicketUpdateRequest
    ) -> TicketResponse:
        try:
            # Validate images if provided
            two_shot_image = data.two_shot.imageUrl if data.two_shot else None
            self._validate_images(data.imageUrl, two_shot_image)

            updated_ticket = await self.repository.update_ticket(
                ticket_id, user_id, data
            )
            if not updated_ticket:
                raise TicketNotFoundError()
            return TicketResponse(**self._resolve_ticket(updated_ticket))
        except TicketNotFoundError:
            raise
        except (ImageTooLargeError, InvalidImageTypeError, InvalidImageError):
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
