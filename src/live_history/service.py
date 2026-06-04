import datetime
import math
from typing import Any, Dict, Optional

from src.live_history.exceptions import InvalidDateError, LiveHistoryUpdateError
from src.live_history.repository import LiveHistoryRepository
from src.live_history.schemas import (
    GlobalLiveHistoryPaginationResponse,
    GlobalLiveHistoryStatsResponse,
    GlobalLiveMemberRankingResponse,
    GlobalSingleMemberLiveHistoryStatsResponse,
    LiveHistoryResponse,
    LiveHistoryStatsResponse,
    LiveHistoryUpdateRequest,
    MemberLiveHistoryStatsResponse,
    WatchedLiveMemberRankingResponse,
)


class LiveHistoryService:
    def __init__(self, repository: LiveHistoryRepository):
        self.repository = repository

    async def get_global_history(
        self,
        page: int = 1,
        limit: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> GlobalLiveHistoryPaginationResponse:
        skip = (page - 1) * limit
        parsed_start, parsed_end = self._parse_date_range(start_date, end_date)
        lives = await self.repository.get_global_history(
            skip=skip, limit=limit, start_date=parsed_start, end_date=parsed_end
        )
        total = await self.repository.get_total_global_history_count(
            start_date=parsed_start, end_date=parsed_end
        )
        total_pages = math.ceil(total / limit) if limit > 0 else 1

        return GlobalLiveHistoryPaginationResponse(
            data=lives, total=total, page=page, limit=limit, total_pages=total_pages
        )

    async def update_watch_duration(
        self, user_id: str, data: LiveHistoryUpdateRequest
    ) -> bool:
        success = await self.repository.update_watch_duration(
            user_id=user_id,
            live_id=data.live_id,
            member_id=data.member_id,
            member_name=data.member_name,
            platform=data.platform,
            ping_duration=data.ping_duration,
            member_nickname=data.member_nickname,
            live_title=data.live_title,
        )
        if not success:
            raise LiveHistoryUpdateError("Failed to update live history")
        return True

    async def get_user_history(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        member_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        skip = (page - 1) * limit

        parsed_start, parsed_end = self._parse_date_range(start_date, end_date)

        if member_id:
            docs = await self.repository.get_history_by_user_and_member(
                user_id, member_id, skip, limit, parsed_start, parsed_end
            )
        else:
            docs = await self.repository.get_history_by_user(
                user_id, skip, limit, parsed_start, parsed_end
            )

        total_count = await self.repository.get_total_history_count(
            user_id, member_id, parsed_start, parsed_end
        )

        last_page = math.ceil(total_count / limit) if limit > 0 else 1
        next_page = page + 1 if page < last_page else None

        history_list = []
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            history_list.append(LiveHistoryResponse(**doc))

        return {
            "data": history_list,
            "meta": {
                "current_page": page,
                "last_page": last_page,
                "total_data": total_count,
                "per_page": limit,
                "next_page": next_page,
            },
        }

    async def get_overall_stats(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> LiveHistoryStatsResponse:
        parsed_start, parsed_end = self._parse_date_range(start_date, end_date)
        stats = await self.repository.get_overall_stats(
            user_id, parsed_start, parsed_end
        )
        longest_watch = await self.repository.get_longest_watch(
            user_id, start_date=parsed_start, end_date=parsed_end
        )
        stats["longest_watch"] = longest_watch
        return LiveHistoryStatsResponse(**stats)

    async def get_member_stats(
        self,
        user_id: str,
        member_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> MemberLiveHistoryStatsResponse:
        parsed_start, parsed_end = self._parse_date_range(start_date, end_date)
        stats = await self.repository.get_member_stats(
            user_id, member_id, parsed_start, parsed_end
        )
        return MemberLiveHistoryStatsResponse(**stats)

    async def get_watched_live_members_ranking(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> WatchedLiveMemberRankingResponse:
        skip = (page - 1) * limit
        parsed_start, parsed_end = self._parse_date_range(start_date, end_date)
        ranking = await self.repository.get_watched_live_members_ranking(
            user_id, skip, limit, parsed_start, parsed_end
        )
        total_count = await self.repository.get_total_watched_live_members_count(
            user_id, parsed_start, parsed_end
        )
        last_page = math.ceil(total_count / limit) if limit > 0 else 1
        next_page = page + 1 if page < last_page else None

        return WatchedLiveMemberRankingResponse(
            data=ranking,
            meta={
                "current_page": page,
                "last_page": last_page,
                "total_data": total_count,
                "per_page": limit,
                "next_page": next_page,
            },
        )

    def _parse_date_range(self, start_date: Optional[str], end_date: Optional[str]):
        parsed_start = None
        parsed_end = None
        if start_date:
            try:
                # Expecting YYYY-MM-DD
                parsed_start = datetime.datetime.strptime(
                    start_date, "%Y-%m-%d"
                ).replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                raise InvalidDateError()
        if end_date:
            try:
                parsed_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59, tzinfo=datetime.timezone.utc
                )
            except ValueError:
                raise InvalidDateError()
        return parsed_start, parsed_end

    async def get_global_stats(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> GlobalLiveHistoryStatsResponse:
        parsed_start, parsed_end = self._parse_date_range(start_date, end_date)
        stats = await self.repository.get_global_overall_stats(
            start_date=parsed_start, end_date=parsed_end
        )
        return GlobalLiveHistoryStatsResponse(**stats)

    async def get_global_members_ranking(
        self,
        page: int = 1,
        limit: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> GlobalLiveMemberRankingResponse:
        skip = (page - 1) * limit
        parsed_start, parsed_end = self._parse_date_range(start_date, end_date)
        ranking = await self.repository.get_global_live_members_ranking(
            skip, limit, start_date=parsed_start, end_date=parsed_end
        )
        total_count = await self.repository.get_total_global_live_members_count(
            start_date=parsed_start, end_date=parsed_end
        )
        last_page = math.ceil(total_count / limit) if limit > 0 else 1
        next_page = page + 1 if page < last_page else None

        return GlobalLiveMemberRankingResponse(
            data=ranking,
            meta={
                "current_page": page,
                "last_page": last_page,
                "total_data": total_count,
                "per_page": limit,
                "next_page": next_page,
            },
        )

    async def get_global_member_history(
        self,
        member_id: str,
        page: int = 1,
        limit: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> GlobalLiveHistoryPaginationResponse:
        skip = (page - 1) * limit
        parsed_start, parsed_end = self._parse_date_range(start_date, end_date)
        lives = await self.repository.get_global_history_by_member(
            member_id, skip, limit, start_date=parsed_start, end_date=parsed_end
        )
        total = await self.repository.get_total_global_history_count_by_member(
            member_id, start_date=parsed_start, end_date=parsed_end
        )
        total_pages = math.ceil(total / limit) if limit > 0 else 1

        return GlobalLiveHistoryPaginationResponse(
            data=lives, total=total, page=page, limit=limit, total_pages=total_pages
        )

    async def get_global_member_stats(
        self,
        member_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> GlobalSingleMemberLiveHistoryStatsResponse:
        parsed_start, parsed_end = self._parse_date_range(start_date, end_date)
        stats = await self.repository.get_global_member_stats(
            member_id, start_date=parsed_start, end_date=parsed_end
        )
        return GlobalSingleMemberLiveHistoryStatsResponse(**stats)
