from typing import List, Optional

from src.config import Settings
from src.logging_config import create_logger
from src.members.constants import Info, Jkt48Members
from src.members.exceptions import MemberFetchError, MemberNotFoundError
from src.members.repository import MemberRepository
from src.members.schemas import (
    MemberDetailResponse,
    MemberListResponse,
    MemberResponse,
    MemberSeedResponse,
)
from src.tickets.schemas import PaginationMeta

logger = create_logger("members_service", __name__)


class MemberService:
    def __init__(
        self,
        repository: MemberRepository,
        config: Settings,
    ):
        self.repository = repository
        self.config = config

    async def seed_members(self) -> MemberSeedResponse:
        """Seed the database with JKT48 member data"""
        try:
            # Clear existing data
            await self.repository.delete_all()

            # Insert new data
            count = await self.repository.insert_many(Jkt48Members.data)

            logger.info(f"Seeded {count} members successfully")
            return MemberSeedResponse(message=Info.MEMBER_DATA_SEEDED, count=count)
        except Exception as e:
            logger.exception(f"Error seeding members: {str(e)}")
            raise MemberFetchError()

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

            member_responses = [MemberResponse(**member) for member in members]

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

    async def get_member_by_id(self, member_id: int) -> MemberDetailResponse:
        """Get a single member by ID"""
        try:
            member = await self.repository.find_by_id(member_id)
            if not member:
                raise MemberNotFoundError()

            return MemberDetailResponse(
                member=MemberResponse(**member), detail=Info.MEMBER_FOUND
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
                member=MemberResponse(**member), detail=Info.MEMBER_FOUND
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
