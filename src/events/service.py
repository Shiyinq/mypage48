import asyncio
from datetime import datetime, timedelta
from math import ceil
from typing import List, Optional

import httpx

from src.config import Settings
from src.events.exceptions import EventFetchError, EventNotFoundError
from src.events.repository import EventsRepository
from src.events.schemas import (
    CalendarEvent,
    Event,
    EventPaginationResponse,
    MemberEventStats,
    PaginationMeta,
)
from src.interfaces import BackgroundTaskRunner
from src.logging_config import create_logger
from src.members.service import MemberService
from src.storage.service import StorageService

logger = create_logger("events_service", __name__)


class EventsService:
    def __init__(
        self,
        repository: EventsRepository,
        background_tasks: BackgroundTaskRunner,
        config: Settings,
        member_service: MemberService,
        storage_service: StorageService,
    ):
        self.repository = repository
        self.background_tasks = background_tasks
        self.config = config
        self.member_service = member_service
        self.storage_service = storage_service

    async def _resolve_event(self, event: dict) -> dict:
        """Resolve event image using storage service."""
        img_url = event.get("imageUrl")
        if img_url:
            if not (img_url.startswith("http") or img_url.startswith("https")):
                res = await self.storage_service.resolve_image_variants(
                    img_url, default_blur_hash=event.get("blurHash")
                )
                event["imageUrl"] = res["url"]
                event["imageUrl_medium"] = res.get("url_medium")
                event["imageUrl_small"] = res.get("url_small")

                if res.get("blurHash"):
                    event["blurHash"] = res["blurHash"]

        if "members" in event:
            await asyncio.gather(
                *[
                    self.member_service._resolve_member(member)
                    for member in event["members"]
                ]
            )

        return event

    async def get_events_paginated(
        self,
        page: int = 1,
        limit: int = 20,
        current_only: bool = False,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> EventPaginationResponse:
        query = {}
        if current_only:
            now = datetime.now()

            # this is because we cant get exac date for event except show setlist from scraper web so default is midnight
            today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Use $or to handle different types of events
            query["$or"] = [
                # 1. Shows with setlistId: must be after right now
                {"date": {"$gte": now}, "setlistId": {"$ne": None}},
                # 2. General events (no setlistId): must be after today midnight
                {"date": {"$gte": today_midnight}, "setlistId": None},
            ]
        elif start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["date"] = date_filter

        try:
            total_data = await self.repository.count_events(query)
            last_page = max(1, ceil(total_data / limit)) if limit > 0 else 1

            # Ensure page is within bounds
            if page < 1:
                page = 1

            skip = (page - 1) * limit

            sort_direction = 1 if current_only else -1
            raw_events = await self.repository.find_events_paginated(
                skip, limit, query, sort_direction
            )

            events_data = []
            for e in raw_events:
                resolved = await self._resolve_event(e)
                events_data.append(Event(**resolved))

            next_page = page + 1 if page < last_page else None

            meta = PaginationMeta(
                current_page=page,
                last_page=last_page,
                total_data=total_data,
                per_page=limit,
                next_page=next_page,
            )

            return EventPaginationResponse(data=events_data, meta=meta)
        except Exception as e:
            logger.exception(f"Failed to fetch paginated events: {str(e)}")
            raise EventFetchError() from e

    async def get_event_by_id(self, event_id: str) -> dict:
        try:
            raw_event = await self.repository.find_event_by_id(event_id)
            if not raw_event:
                raise EventNotFoundError()

            # Fetch realtime detail if applicable (EXCLUSIVE, SHOW)
            await self._fetch_and_inject_realtime_data(event_id, raw_event)

            resolved = await self._resolve_event(raw_event)
            return resolved
        except EventNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Failed to fetch event by id {event_id}: {str(e)}")
            raise EventFetchError() from e

    async def get_calendar_events(self, year: int, month: int) -> List[CalendarEvent]:
        # 1. Start Date (Start of the week containing the 1st)
        # We assume Sunday as the start of the week.
        first_of_month = datetime(year, month, 1)
        # weekday(): Mon=0, ..., Sat=5, Sun=6
        # padding needed for Sunday start: (weekday + 1) % 7
        days_to_subtract = (first_of_month.weekday() + 1) % 7
        start_date = first_of_month - timedelta(days=days_to_subtract)
        # Ensure time is 00:00:00
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # 2. End Date (Fixed 42 days / 6 weeks from start)
        # The frontend renders a fixed 6-row grid (7 cols * 6 rows = 42 days).
        # We need to fetch enough data to cover this entire grid, including "overflow" into next month.
        end_date = start_date + timedelta(days=42)
        # Ensure time is 23:59:59 (technically end_date is exclusive in range math usually, but $lte uses inclusive)
        # Let's subtract a microsecond to be safe if we treat it as bound, or just set to end of day.
        # Here we set exactly 42 days later.
        end_date = end_date - timedelta(microseconds=1)

        try:
            raw_events = await self.repository.find_events_by_date_range(
                start_date, end_date
            )
            results = [CalendarEvent(**e) for e in raw_events]

            birthdays = await self.member_service.get_birthdays_by_date_range(
                start_date, end_date
            )

            for b in birthdays:
                results.append(
                    CalendarEvent(
                        id=b["id"],
                        title=b["name"],
                        date=b["date"],
                        url=f"/member/detail/id/{b['id']}",
                        isBirthday=True,
                        setlistId=None,
                        seitansaiMembers=None,
                    )
                )

            return results
        except Exception as e:
            logger.exception(f"Failed to fetch calendar events: {str(e)}")
            raise EventFetchError() from e

    async def get_events_for_member(self, member_id: str) -> List[dict]:
        """Get all events for a specific member to calculate attendance stats."""
        try:
            return await self.repository.find_events_by_member_id(member_id)
        except Exception as e:
            logger.exception(f"Failed to fetch events for member {member_id}: {str(e)}")
            return []

    async def get_member_event_stats(self, member_id: str) -> MemberEventStats:
        """Get show statistics for a member."""
        try:
            stats_data = await self.repository.get_member_event_stats(member_id)
            return MemberEventStats(**stats_data)
        except Exception as e:
            logger.exception(
                f"Failed to fetch event stats for member {member_id}: {str(e)}"
            )
            return MemberEventStats()

    async def get_member_events_paginated(
        self, member_id: str, page: int = 1, limit: int = 20
    ) -> EventPaginationResponse:
        """Get events for a member with pagination."""
        try:
            total_data = await self.repository.count_member_events(member_id)
            last_page = max(1, ceil(total_data / limit)) if limit > 0 else 1

            if page < 1:
                page = 1

            skip = (page - 1) * limit

            raw_events = await self.repository.find_events_by_member_id_detailed(
                member_id, skip=skip, limit=limit
            )

            events_data = []
            for e in raw_events:
                resolved = await self._resolve_event(e)
                events_data.append(Event(**resolved))

            next_page = page + 1 if page < last_page else None

            meta = PaginationMeta(
                current_page=page,
                last_page=last_page,
                total_data=total_data,
                per_page=limit,
                next_page=next_page,
            )

            return EventPaginationResponse(data=events_data, meta=meta)
        except Exception as e:
            logger.exception(
                f"Failed to fetch paginated events for member {member_id}: {str(e)}"
            )
            return EventPaginationResponse(
                data=[],
                meta=PaginationMeta(
                    current_page=page,
                    last_page=1,
                    total_data=0,
                    per_page=limit,
                    next_page=None,
                ),
            )

    async def get_member_events_detailed(self, member_id: str) -> List[Event]:
        """Get all events for a member with full detail (images, resolved)."""
        try:
            raw_events = await self.repository.find_events_by_member_id_detailed(
                member_id
            )
            events_data = []
            for e in raw_events:
                resolved = await self._resolve_event(e)
                events_data.append(Event(**resolved))
            return events_data
        except Exception as e:
            logger.exception(
                f"Failed to fetch detailed events for member {member_id}: {str(e)}"
            )
            return []

    async def _fetch_and_inject_realtime_data(self, event_id: str, raw_event: dict):
        raw_data = raw_event.get("raw_data", {})
        short_data = raw_data.get("short", {})
        ref_code = short_data.get("reference_code")
        event_type = raw_event.get("type")

        if not ref_code:
            return

        url = None
        if event_type == "EXCLUSIVE":
            url = f"https://jkt48.com/api/v1/exclusives/{ref_code}"
        elif event_type == "SHOW":
            url = f"https://jkt48.com/api/v1/theater-shows/{ref_code}?lang=id"

        if url:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                "Referer": f"https://jkt48.com/purchase/schedule/show?code={ref_code}"
                if event_type == "SHOW"
                else f"https://jkt48.com/purchase/exclusive?code={ref_code}",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    res = await client.get(url, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("status") and "data" in data:
                            if "raw_data" not in raw_event:
                                raw_event["raw_data"] = {}
                            raw_event["raw_data"]["detail"] = data["data"]

                            # Cache it in DB for fallback without overwriting 'short'
                            await self.repository.update_event_raw_data_detail(
                                event_id, data["data"]
                            )

                            if event_type == "SHOW":
                                await self._sync_show_members_dynamically(
                                    event_id, raw_event, data["data"]
                                )

                except Exception as exc:
                    logger.warning(
                        f"Failed to fetch realtime data for {ref_code}: {exc}"
                    )

    async def _sync_show_members_dynamically(
        self, event_id: str, raw_event: dict, show_detail: dict
    ):
        jkt_members = show_detail.get("jkt48_member", [])
        bday_names = show_detail.get("birthday_member_name", [])

        if jkt_members and len(raw_event.get("members", [])) != len(jkt_members):
            active_members = await self.member_service.repository.find_all_active()
            name_to_member = {m["name"].lower(): m for m in active_members}

            member_ids = []
            resolved_members = []

            for jm in jkt_members:
                jm_name = jm.get("name", "").strip().lower()
                current_id = str(jm.get("member_id", ""))

                db_member = name_to_member.get(jm_name)
                if not db_member:
                    # fallback partial match
                    for key, m in name_to_member.items():
                        if jm_name in key or key in jm_name:
                            db_member = m
                            break

                legacy_id = db_member["id"] if db_member else current_id
                member_ids.append(legacy_id)

                if db_member:
                    resolved_members.append(db_member)

            seitansai_ids = []
            if bday_names:
                for name in bday_names:
                    name_lower = name.lower()
                    db_member = name_to_member.get(name_lower)
                    if not db_member:
                        for key, m in name_to_member.items():
                            if name_lower in key or key in name_lower:
                                db_member = m
                                break
                    if db_member:
                        seitansai_ids.append(db_member["id"])

            if member_ids:
                await self.repository.update_event_live_members(
                    event_id, member_ids, seitansai_ids
                )

                # Inject so it resolves in the current request
                raw_event["members"] = resolved_members
                raw_event["memberIds"] = member_ids
                raw_event["seitansaiIds"] = seitansai_ids

                # Aggregate creates seitansaiMembers as list of names, let's inject it too
                seitansai_names = [
                    m["name"] for m in resolved_members if m["id"] in seitansai_ids
                ]
                raw_event["seitansaiMembers"] = seitansai_names
                raw_event["totalMembers"] = len(member_ids)
