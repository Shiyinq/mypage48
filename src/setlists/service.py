from typing import Optional, List

from src.config import Settings
from src.logging_config import create_logger
from src.setlists.repository import SetlistsRepository
from src.setlists.schemas import (
    SetlistResponse,
    SetlistWithStats,
    SetlistListResponse,
    SetlistSeedResponse,
    SetlistDetailResponse,
    SetlistDetailStats,
    WatchedStats,
    TicketItem,
    TicketEvent,
    TicketSeat,
)
from src.setlists.constants import Info, Jkt48Setlists
from src.setlists.exceptions import SetlistNotFoundError, SetlistFetchError

logger = create_logger("setlists_service", __name__)


class SetlistsService:
    def __init__(
        self,
        repository: SetlistsRepository,
        config: Settings,
    ):
        self.repository = repository
        self.config = config

    async def seed_setlists(self) -> SetlistSeedResponse:
        """Seed the database with JKT48 setlist data"""
        try:
            # Clear existing data
            await self.repository.delete_all()

            # Insert new data
            count = await self.repository.insert_many(Jkt48Setlists.data)

            logger.info(f"Seeded {count} setlists successfully")
            return SetlistSeedResponse(message=Info.SETLIST_DATA_SEEDED, count=count)
        except Exception as e:
            logger.exception(f"Error seeding setlists: {str(e)}")
            raise SetlistFetchError()

    async def get_all_setlists(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        setlist_type: Optional[str] = None,
        active: Optional[bool] = None,
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
            )
            total = await self.repository.count(setlist_type, active)

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
                        **{k: v for k, v in setlist.items() if k not in ("_id", "count")},
                        watched=watched,
                    )
                )

            return SetlistListResponse(
                total=total,
                maxAttendance=max_attendance if user_id else 0,
                setlists=setlist_responses
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

            return SetlistResponse(
                **{k: v for k, v in setlist.items() if k != "_id"}
            )
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

            return SetlistResponse(
                **{k: v for k, v in setlist.items() if k != "_id"}
            )
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

                tickets.append(TicketItem(
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
                ))

            # Compute stats
            total_spent = sum(t.price for t in tickets)
            avg_price = total_spent / len(tickets) if tickets else 0

            # Calculate top row
            row_counts: dict[str, int] = {}
            for t in tickets:
                row = t.seat.section.upper()[0] if t.seat.section else ""
                if row:
                    row_counts[row] = row_counts.get(row, 0) + 1
            top_row = max(row_counts.items(), key=lambda x: x[1])[0] if row_counts else None

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
                k: v for k, v in result.items()
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

