import asyncio
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
from src.storage.service import StorageService
from src.utils import cleanse_image_url

logger = create_logger("setlists_service", __name__)


class SetlistsService:
    def __init__(
        self,
        repository: SetlistsRepository,
        config: Settings,
        storage_service: StorageService,
    ):
        self.repository = repository
        self.config = config
        self.storage_service = storage_service

    async def _resolve_setlist(self, setlist: dict) -> dict:
        """Resolve setlist image using storage service."""
        img_url = setlist.get("imageUrl")
        if img_url:
            if not (img_url.startswith("http") or img_url.startswith("https")):
                res = await self.storage_service.resolve_image_variants(img_url)
                setlist["imageUrl"] = res["url"]
                setlist["imageUrl_medium"] = res.get("url_medium")
                setlist["imageUrl_small"] = res.get("url_small")

                if res.get("blurHash"):
                    # If it was missing in the DB but found in storage, update the DB
                    if not setlist.get("blurHash"):
                        try:
                            await self.repository.update_one(
                                setlist["setlistId"], {"blurHash": res["blurHash"]}
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to JIT update blurHash for setlist {setlist.get('setlistId')}: {e}"
                            )
                    setlist["blurHash"] = res["blurHash"]
        return setlist

    async def get_all_setlists(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        setlist_type: Optional[str] = None,
        active: Optional[bool] = None,
        search: Optional[str] = None,
        year: Optional[int] = None,
        start_month: Optional[int] = None,
        end_month: Optional[int] = None,
        is_all_data: bool = False,
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
                year=year,
                start_month=start_month,
                end_month=end_month,
                is_all_data=is_all_data,
            )
            total = await self.repository.count(setlist_type, active, search)

            setlist_responses = []
            for setlist in setlists:
                # Resolve image URLs
                resolved = await self._resolve_setlist(setlist)

                count = resolved.get("count", 0)
                percentage = (count / max_attendance) * 100 if max_attendance > 0 else 0
                is_most_watched = count == max_attendance and count > 0

                # Create watched stats object
                watched = WatchedStats(
                    count=count,
                    percentage=round(percentage, 1),
                    isMostWatched=is_most_watched,
                )

                # Prepare data for model, removing MongoDB internal fields
                model_data = {
                    k: v for k, v in resolved.items() if k not in ("_id", "count")
                }

                setlist_responses.append(
                    SetlistWithStats(
                        **model_data,
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

            resolved = await self._resolve_setlist(setlist)
            response_data = {k: v for k, v in resolved.items() if k != "_id"}
            return SetlistResponse(**response_data)
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

            resolved = await self._resolve_setlist(setlist)
            response_data = {k: v for k, v in resolved.items() if k != "_id"}
            return SetlistResponse(**response_data)
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
        year: Optional[int] = None,
        start_month: Optional[int] = None,
        end_month: Optional[int] = None,
        is_all_data: bool = False,
    ) -> SetlistDetailResponse:
        """Get setlist detail with user's tickets and computed statistics"""
        try:
            # Get setlist with matched tickets
            result = await self.repository.find_with_tickets(
                setlist_id,
                user_id,
                year=year,
                start_month=start_month,
                end_month=end_month,
                is_all_data=is_all_data,
            )
            if not result:
                raise SetlistNotFoundError()

            # Get max attendance for percentage calculation
            max_attendance = await self.repository.get_max_attendance(
                user_id,
                year=year,
                start_month=start_month,
                end_month=end_month,
                is_all_data=is_all_data,
            )

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
            total_spent = sum(
                t.get("price", 0) + (t.get("two_shot") or {}).get("price", 0)
                for t in matched_tickets
            )
            avg_price = total_spent / len(tickets) if tickets else 0

            # Calculate top row and top row count
            row_counts: dict[str, int] = {}
            for t in tickets:
                row = t.seat.section.upper()[0] if t.seat.section else ""
                if row:
                    row_counts[row] = row_counts.get(row, 0) + 1

            top_row = None
            top_row_count = 0
            if row_counts:
                top_row, top_row_count = max(row_counts.items(), key=lambda x: x[1])

            # First and last dates and seats (tickets are sorted newest to oldest)
            first_date = tickets[-1].event.date if tickets else None
            last_date = tickets[0].event.date if tickets else None
            first_seat = (
                f"{tickets[-1].seat.section}-{tickets[-1].seat.number}"
                if tickets and tickets[-1].seat.section
                else None
            )
            last_seat = (
                f"{tickets[0].seat.section}-{tickets[0].seat.number}"
                if tickets and tickets[0].seat.section
                else None
            )

            # Count total 2-shots and build 2-shots history
            two_shots_dict = {}
            total_2shot = 0
            for t in matched_tickets:
                two_shot = t.get("two_shot")
                if two_shot:
                    total_2shot += 1
                    name = two_shot.get("member_name")
                    if name:
                        if name not in two_shots_dict:
                            two_shots_dict[name] = {
                                "name": name,
                                "count": 0,
                                "imageUrl": two_shot.get("imageUrl"),
                                "blurHash": two_shot.get("blurHash"),
                            }
                        two_shots_dict[name]["count"] += 1

            two_shots_list = sorted(
                two_shots_dict.values(), key=lambda x: x["count"], reverse=True
            )

            # Resolve image variants for 2-shots
            async def _resolve_twoshot(item: dict):
                image_url = item.get("imageUrl")
                item["imageUrl_medium"] = None
                item["imageUrl_small"] = None

                if image_url:
                    if not image_url.startswith("http"):
                        variants = await self.storage_service.resolve_image_variants(
                            image_url
                        )
                        item["imageUrl"] = variants["url"]
                        item["imageUrl_medium"] = variants.get("url_medium")
                        item["imageUrl_small"] = variants.get("url_small")
                        item["blurHash"] = variants.get("blurHash") or item.get(
                            "blurHash"
                        )
                return item

            if two_shots_list:
                tasks = [_resolve_twoshot(item) for item in two_shots_list]
                two_shots_list = list(await asyncio.gather(*tasks))

            stats = SetlistDetailStats(
                totalAttendance=count,
                totalSpent=total_spent,
                avgPrice=round(avg_price),
                topRow=top_row,
                topRowCount=top_row_count,
                firstDate=first_date,
                lastDate=last_date,
                firstSeat=first_seat,
                lastSeat=last_seat,
                total2Shot=total_2shot,
            )

            resolved = await self._resolve_setlist(result)
            # Build response excluding internal fields
            setlist_fields = {
                k: v
                for k, v in resolved.items()
                if k not in ("_id", "count", "matched_tickets")
            }

            return SetlistDetailResponse(
                **setlist_fields,
                watched=watched,
                stats=stats,
                tickets=tickets,
                twoShots=two_shots_list,
            )

        except SetlistNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error fetching setlist detail {setlist_id}: {str(e)}")
            raise SetlistFetchError()

    async def create_setlist(self, data: SetlistCreateRequest) -> SetlistResponse:
        """Create a new setlist"""
        try:
            # Generate setlistId from title: lowercase, no spaces, keep other characters
            setlist_id = data.title.lower().replace(" ", "")

            setlist_data = {
                "setlistId": setlist_id,
                **data.model_dump(exclude_none=True),
            }

            await self.repository.insert_one(setlist_data)
            return await self.get_setlist_by_id(setlist_id)
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
                # Cleanse image URL if provided (convert full URL to relative path)
                if "imageUrl" in update_data:
                    update_data["imageUrl"] = cleanse_image_url(update_data["imageUrl"])

                # 1. Handle image cleanup or rename
                has_new_img = (
                    "imageUrl" in update_data
                    and existing.get("imageUrl")
                    and update_data["imageUrl"] != existing["imageUrl"]
                )
                title_changed = (
                    "title" in update_data and update_data["title"] != existing["title"]
                )

                if has_new_img:
                    # New image uploaded - delete the old one
                    await self.storage_service.delete_image(existing["imageUrl"])
                elif title_changed and existing.get("imageUrl"):
                    # No new image, but title changed - rename the existing image file
                    new_img_path = await self.storage_service.rename_image(
                        existing["imageUrl"], update_data["title"], "setlist"
                    )
                    if new_img_path != existing["imageUrl"]:
                        update_data["imageUrl"] = new_img_path

                setlist = await self.repository.update_one(setlist_id, update_data)
            else:
                setlist = existing

            if not setlist:
                raise SetlistNotFoundError()

            resolved = await self._resolve_setlist(setlist)
            response_data = {k: v for k, v in resolved.items() if k != "_id"}
            return SetlistResponse(**response_data)
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

            # Cleanup image from R2
            if existing.get("imageUrl"):
                await self.storage_service.delete_image(existing["imageUrl"])

            return MessageResponse(message=Info.SETLIST_DELETED)
        except SetlistNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error deleting setlist {setlist_id}: {str(e)}")
            raise SetlistFetchError()
