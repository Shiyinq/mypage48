import asyncio
from datetime import datetime
from typing import List, Optional

from src.config import Settings
from src.logging_config import create_logger
from src.members.constants import Info
from src.members.exceptions import MemberFetchError, MemberNotFoundError
from src.members.repository import MemberRepository
from src.members.schemas import (
    BirthdayResponse,
    MemberCreateRequest,
    MemberDetailResponse,
    MemberListResponse,
    MemberResponse,
    MemberUpdateRequest,
    MessageResponse,
)
from src.storage.service import StorageService
from src.tickets.schemas import PaginationMeta

logger = create_logger("members_service", __name__)


class MemberService:
    def __init__(
        self,
        repository: MemberRepository,
        config: Settings,
        storage_service: StorageService,
    ):
        self.repository = repository
        self.config = config
        self.storage_service = storage_service

    async def _resolve_member(self, member: dict) -> dict:
        """Resolve member image using storage service (external)."""
        if member.get("img"):
            res = await self.storage_service.resolve_external_media(member["img"])
            member["img"] = res["url"]
            member["img_medium"] = res.get("url_medium")
            member["img_small"] = res.get("url_small")
            if res.get("blurHash"):
                member["blurHash"] = res["blurHash"]
        return member

    async def get_all_members(
        self,
        page: int = 1,
        limit: int = 20,
        generation: Optional[str] = None,
        search: Optional[str] = None,
    ) -> MemberListResponse:
        """Get all members with optional filtering"""
        try:
            skip = (page - 1) * limit
            members = await self.repository.find_all(skip, limit, generation, search)
            total = await self.repository.count(generation, search)

            resolved_members = await asyncio.gather(
                *(self._resolve_member(member) for member in members)
            )

            member_responses = [MemberResponse(**member) for member in resolved_members]

            last_page = (total + limit - 1) // limit if limit > 0 else 1
            if last_page < 1:
                last_page = 1
            next_page = page + 1 if page < last_page else None

            meta = PaginationMeta(
                current_page=page,
                last_page=last_page,
                total_data=total,
                per_page=limit,
                next_page=next_page,
            )

            return MemberListResponse(data=member_responses, meta=meta)
        except Exception as e:
            logger.exception(f"Error fetching members: {str(e)}")
            raise MemberFetchError()

    async def get_member_by_id(self, member_id: str) -> MemberDetailResponse:
        """Get a single member by ID"""
        try:
            member = await self.repository.find_by_id(member_id)
            if not member:
                raise MemberNotFoundError()

            return MemberDetailResponse(
                member=MemberResponse(**(await self._resolve_member(member))),
                detail=Info.MEMBER_FOUND,
            )
        except MemberNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error fetching member {member_id}: {str(e)}")
            raise MemberFetchError()

    async def get_member_by_nickname(self, nickname: str) -> MemberDetailResponse:
        """Get a single member by nickname"""
        try:
            member = await self.repository.find_by_nickname(nickname)
            if not member:
                raise MemberNotFoundError()

            return MemberDetailResponse(
                member=MemberResponse(**(await self._resolve_member(member))),
                detail=Info.MEMBER_FOUND,
            )
        except MemberNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error fetching member {nickname}: {str(e)}")
            raise MemberFetchError()

    async def get_generations(self) -> List[str]:
        """Get list of all generations"""
        try:
            return await self.repository.get_generations()
        except Exception as e:
            logger.exception(f"Error fetching generations: {str(e)}")
            raise MemberFetchError()

    async def create_member(self, data: MemberCreateRequest) -> MemberResponse:
        """Create a new member"""
        try:
            next_id = await self.repository.get_next_id()
            now = datetime.now()

            member_data = {
                "id": str(next_id),
                **data.model_dump(exclude_none=True),
                "createdAt": now,
                "updatedAt": now,
            }

            member = await self.repository.insert_one(member_data)
            return MemberResponse(**(await self._resolve_member(member)))
        except Exception as e:
            logger.exception(f"Error creating member: {str(e)}")
            raise MemberFetchError()

    async def update_member(
        self, member_id: str, data: MemberUpdateRequest
    ) -> MemberResponse:
        """Update an existing member"""
        try:
            # Check if member exists
            existing = await self.repository.find_by_id(member_id)
            if not existing:
                raise MemberNotFoundError()

            update_data = data.model_dump(exclude_none=True)
            if update_data:
                update_data["updatedAt"] = datetime.now()
                member = await self.repository.update_one(member_id, update_data)
            else:
                member = existing

            return MemberResponse(**(await self._resolve_member(member)))
        except MemberNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error updating member {member_id}: {str(e)}")
            raise MemberFetchError()

    async def delete_member(self, member_id: str) -> MessageResponse:
        """Delete a member by ID"""
        try:
            # Check if member exists
            existing = await self.repository.find_by_id(member_id)
            if not existing:
                raise MemberNotFoundError()

            deleted = await self.repository.delete_one(member_id)
            if not deleted:
                raise MemberFetchError()

            return MessageResponse(message=Info.MEMBER_DELETED)
        except MemberNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error deleting member {member_id}: {str(e)}")
            raise MemberFetchError()

    async def get_upcoming_birthdays(self) -> List[BirthdayResponse]:
        """Get members with upcoming birthdays in the next 30 days"""
        try:
            members = await self.repository.find_all_active()
            upcoming = []
            today = datetime.now().date()

            months_map = {
                "Januari": 1,
                "Februari": 2,
                "Maret": 3,
                "April": 4,
                "Mei": 5,
                "Juni": 6,
                "Juli": 7,
                "Agustus": 8,
                "September": 9,
                "Oktober": 10,
                "November": 11,
                "Desember": 12,
            }

            async def _resolve_upcoming(m_data, d_until, m_age):
                res = BirthdayResponse(
                    id=m_data.get("id", ""),
                    name=m_data.get("name", ""),
                    active=m_data.get("active", True),
                    img=m_data.get("img"),
                    birthdate=m_data.get("birthdate", ""),
                    days_until=d_until,
                    age=m_age,
                    member_type=m_data.get("member_type", "JKT48"),
                )
                if res.img:
                    res.img = await self.storage_service.resolve_external_url(res.img)
                return res

            tasks = []
            for member in members:
                if not member.get("birthdate"):
                    continue

                try:
                    # Parse birthdate "DD Month YYYY" (e.g., "16 Januari 1999")
                    parts = member["birthdate"].split()
                    if len(parts) != 3:
                        continue

                    day = int(parts[0])
                    month_str = parts[1]
                    year = int(parts[2])

                    if month_str not in months_map:
                        continue

                    month = months_map[month_str]

                    # Calculate next birthday
                    current_year_birthday = datetime(today.year, month, day).date()
                    next_birthday = current_year_birthday

                    if current_year_birthday < today:
                        next_birthday = datetime(today.year + 1, month, day).date()

                    days_until = (next_birthday - today).days

                    # Check if within next 30 days
                    if 0 <= days_until <= 30:
                        age = next_birthday.year - year
                        tasks.append(_resolve_upcoming(member, days_until, age))
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Error parsing birthdate for member {member.get('name')}: {e}"
                    )
                    continue

            if tasks:
                upcoming = list(await asyncio.gather(*tasks))

            # Sort by days until birthday
            upcoming.sort(key=lambda x: x.days_until)
            return upcoming

        except Exception as e:
            logger.exception(f"Error fetching upcoming birthdays: {str(e)}")
            raise MemberFetchError()

    async def get_birthdays_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[dict]:
        """Get members with birthdays within the specified date range"""
        try:
            members = await self.repository.find_all_active()
            results = []

            months_map = {
                "Januari": 1,
                "Februari": 2,
                "Maret": 3,
                "April": 4,
                "Mei": 5,
                "Juni": 6,
                "Juli": 7,
                "Agustus": 8,
                "September": 9,
                "Oktober": 10,
                "November": 11,
                "Desember": 12,
            }

            async def _resolve_range(m_data, b_date):
                return {
                    "id": m_data.get("id", ""),
                    "name": m_data.get("name", ""),
                    "date": b_date,
                    "img": await self.storage_service.resolve_external_url(
                        m_data.get("img")
                    ),
                    "active": m_data.get("active", True),
                    "member_type": m_data.get("member_type", "JKT48"),
                }

            tasks = []
            for member in members:
                if not member.get("birthdate"):
                    continue

                try:
                    # Parse birthdate "DD Month YYYY" (e.g., "16 Januari 1999")
                    parts = member["birthdate"].split()
                    if len(parts) != 3:
                        continue

                    day = int(parts[0])
                    month_str = parts[1]
                    # year = int(parts[2]) # Birth year not strictly needed for "is birthday on date X" check

                    if month_str not in months_map:
                        continue

                    month = months_map[month_str]

                    # We need to check if this birthday (month, day) occurs in any year covered by start_date -> end_date
                    # Ranges are typically small (42 days), so it might span at most 2 years (e.g. Dec to Jan).

                    # Check for each year in the range [start_date.year, end_date.year]
                    for year_to_check in range(start_date.year, end_date.year + 1):
                        try:
                            birthday_date = datetime(year_to_check, month, day)
                            if start_date <= birthday_date <= end_date:
                                tasks.append(_resolve_range(member, birthday_date))
                        except ValueError:
                            # Handle Feb 29 on non-leap years if applicable, etc.
                            continue

                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Error parsing birthdate for member {member.get('name')}: {e}"
                    )
                    continue

            if tasks:
                results = list(await asyncio.gather(*tasks))

            return results

        except Exception as e:
            logger.exception(f"Error fetching birthdays by range: {str(e)}")
            return []
