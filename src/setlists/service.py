import uuid
from typing import List, Optional

from src.config import Settings
from src.logging_config import create_logger
from src.setlists.constants import Info
from src.setlists.exceptions import SetlistFetchError, SetlistNotFoundError
from src.setlists.repository import SetlistsRepository
from src.setlists.schemas import (
    MessageResponse,
    SetlistCreateRequest,
    SetlistDetailResponse,
    SetlistDetailStats,
    SetlistListResponse,
    SetlistResponse,
    SetlistUpdateRequest,
    SetlistWithStats,
    TicketEvent,
    TicketItem,
    TicketSeat,
    WatchedStats,
)

logger = create_logger("setlists_service", __name__)


class SetlistsService:
    def __init__(
        self,
        repository: SetlistsRepository,
        config: Settings,
    ):
        self.repository = repository
        self.config = config

    async def get_all_setlists(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        setlist_type: Optional[str] = None,
        active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> SetlistListResponse:
        """Get all setlists with optional filtering and user statistics"""
        try:
            # Use aggregation to get setlists with ticket counts
            setlists, max_attendance = await self.repository.find_all_with_stats(
                user_id=user_id,
                skip=skip,
                limit=limit,
                setlist_type=setlist_type,
                active=active,
                search=search,
            )
            total = await self.repository.count(setlist_type, active, search)

            setlist_responses = []
            for setlist in setlists:
                count = setlist.get("count", 0)
                percentage = (count / max_attendance) * 100 if max_attendance > 0 else 0
                is_most_watched = count == max_attendance and count > 0

                # Create watched stats object
                watched = WatchedStats(
                    count=count,
                    percentage=round(percentage, 1),
                    isMostWatched=is_most_watched,
                )

                setlist_responses.append(
                    SetlistWithStats(
                        **{
                            k: v
                            for k, v in setlist.items()
                            if k not in ("_id", "count")
                        },
                        watched=watched,
                    )
                )

            return SetlistListResponse(
                total=total,
                maxAttendance=max_attendance if user_id else 0,
                setlists=setlist_responses,
            )
        except Exception as e:
            logger.exception(f"Error fetching setlists: {str(e)}")
            raise SetlistFetchError()

    async def get_setlist_by_id(self, setlist_id: str) -> SetlistResponse:
        """Get a single setlist by setlistId"""
        try:
            setlist = await self.repository.find_by_setlist_id(setlist_id)
            if not setlist:
                raise SetlistNotFoundError()

            return SetlistResponse(**{k: v for k, v in setlist.items() if k != "_id"})
        except SetlistNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error fetching setlist {setlist_id}: {str(e)}")
            raise SetlistFetchError()

    async def get_setlist_by_title(self, title: str) -> SetlistResponse:
        """Get a single setlist by title"""
        try:
            setlist = await self.repository.find_by_title(title)
            if not setlist:
                raise SetlistNotFoundError()

            return SetlistResponse(**{k: v for k, v in setlist.items() if k != "_id"})
        except SetlistNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error fetching setlist {title}: {str(e)}")
            raise SetlistFetchError()

    async def get_types(self) -> List[str]:
        """Get list of all setlist types"""
        try:
            return await self.repository.get_types()
        except Exception as e:
            logger.exception(f"Error fetching types: {str(e)}")
            raise SetlistFetchError()

    async def get_setlist_detail(
        self,
        setlist_id: str,
        user_id: str,
    ) -> SetlistDetailResponse:
        """Get setlist detail with user's tickets and computed statistics"""
        try:
            # Get setlist with matched tickets
            result = await self.repository.find_with_tickets(setlist_id, user_id)
            if not result:
                raise SetlistNotFoundError()

            # Get max attendance for percentage calculation
            max_attendance = await self.repository.get_max_attendance(user_id)

            # Extract tickets from result
            matched_tickets = result.get("matched_tickets", [])
            count = result.get("count", 0)

            # Calculate watched stats
            percentage = (count / max_attendance) * 100 if max_attendance > 0 else 0
            is_most_watched = count == max_attendance and count > 0

            watched = WatchedStats(
                count=count,
                percentage=round(percentage, 1),
                isMostWatched=is_most_watched,
            )

            # Build ticket items list
            tickets = []
            for t in matched_tickets:
                event_data = t.get("event", {})
                seat_data = t.get("seat", {})

                tickets.append(
                    TicketItem(
                        ticketId=t.get("ticketId", ""),
                        event=TicketEvent(
                            title=event_data.get("title", ""),
                            date=event_data.get("date", ""),
                            time=event_data.get("time", ""),
                        ),
                        seat=TicketSeat(
                            section=seat_data.get("section", ""),
                            number=seat_data.get("number", 0),
                        ),
                        price=t.get("price", 0),
                        notes=t.get("notes"),
                    )
                )

            # Compute stats
            total_spent = sum(t.price for t in tickets)
            avg_price = total_spent / len(tickets) if tickets else 0

            # Calculate top row
            row_counts: dict[str, int] = {}
            for t in tickets:
                row = t.seat.section.upper()[0] if t.seat.section else ""
                if row:
                    row_counts[row] = row_counts.get(row, 0) + 1
            top_row = (
                max(row_counts.items(), key=lambda x: x[1])[0] if row_counts else None
            )

            # First and last dates
            first_date = tickets[0].event.date if tickets else None
            last_date = tickets[-1].event.date if tickets else None

            stats = SetlistDetailStats(
                totalAttendance=count,
                totalSpent=total_spent,
                avgPrice=round(avg_price),
                topRow=top_row,
                firstDate=first_date,
                lastDate=last_date,
            )

            # Build response excluding internal fields
            setlist_fields = {
                k: v
                for k, v in result.items()
                if k not in ("_id", "count", "matched_tickets")
            }

            return SetlistDetailResponse(
                **setlist_fields,
                watched=watched,
                stats=stats,
                tickets=tickets,
            )

        except SetlistNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error fetching setlist detail {setlist_id}: {str(e)}")
            raise SetlistFetchError()

    async def create_setlist(self, data: SetlistCreateRequest) -> SetlistResponse:
        """Create a new setlist"""
        try:
            setlist_id = str(uuid.uuid4())

            setlist_data = {
                "setlistId": setlist_id,
                **data.model_dump(exclude_none=True),
            }

            setlist = await self.repository.insert_one(setlist_data)
            return SetlistResponse(**{k: v for k, v in setlist.items() if k != "_id"})
        except Exception as e:
            logger.exception(f"Error creating setlist: {str(e)}")
            raise SetlistFetchError()

    async def update_setlist(
        self, setlist_id: str, data: SetlistUpdateRequest
    ) -> SetlistResponse:
        """Update an existing setlist"""
        try:
            # Check if setlist exists
            existing = await self.repository.find_by_setlist_id(setlist_id)
            if not existing:
                raise SetlistNotFoundError()

            update_data = data.model_dump(exclude_none=True)
            if update_data:
                setlist = await self.repository.update_one(setlist_id, update_data)
            else:
                setlist = existing

            return SetlistResponse(**{k: v for k, v in setlist.items() if k != "_id"})
        except SetlistNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error updating setlist {setlist_id}: {str(e)}")
            raise SetlistFetchError()

    async def delete_setlist(self, setlist_id: str) -> MessageResponse:
        """Delete a setlist by ID"""
        try:
            # Check if setlist exists
            existing = await self.repository.find_by_setlist_id(setlist_id)
            if not existing:
                raise SetlistNotFoundError()

            deleted = await self.repository.delete_one(setlist_id)
            if not deleted:
                raise SetlistFetchError()

            return MessageResponse(message=Info.SETLIST_DELETED)
        except SetlistNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error deleting setlist {setlist_id}: {str(e)}")
            raise SetlistFetchError()
