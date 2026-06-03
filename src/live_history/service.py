import math
from typing import Any, Dict, Optional

from src.live_history.exceptions import LiveHistoryUpdateError
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
        self, page: int = 1, limit: int = 20
    ) -> GlobalLiveHistoryPaginationResponse:
        skip = (page - 1) * limit
        lives = await self.repository.get_global_history(skip=skip, limit=limit)
        total = await self.repository.get_total_global_history_count()
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
    ) -> Dict[str, Any]:
        skip = (page - 1) * limit

        if member_id:
            docs = await self.repository.get_history_by_user_and_member(
                user_id, member_id, skip, limit
            )
        else:
            docs = await self.repository.get_history_by_user(user_id, skip, limit)

        total_count = await self.repository.get_total_history_count(user_id, member_id)

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

    async def get_overall_stats(self, user_id: str) -> LiveHistoryStatsResponse:
        stats = await self.repository.get_overall_stats(user_id)
        longest_watch = await self.repository.get_longest_watch(user_id)
        stats["longest_watch"] = longest_watch
        return LiveHistoryStatsResponse(**stats)

    async def get_member_stats(
        self, user_id: str, member_id: str
    ) -> MemberLiveHistoryStatsResponse:
        stats = await self.repository.get_member_stats(user_id, member_id)
        return MemberLiveHistoryStatsResponse(**stats)

    async def get_watched_live_members_ranking(
        self, user_id: str, page: int = 1, limit: int = 20
    ) -> WatchedLiveMemberRankingResponse:
        skip = (page - 1) * limit
        ranking = await self.repository.get_watched_live_members_ranking(
            user_id, skip, limit
        )
        total_count = await self.repository.get_total_watched_live_members_count(
            user_id
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

    async def get_global_stats(self) -> GlobalLiveHistoryStatsResponse:
        stats = await self.repository.get_global_overall_stats()
        return GlobalLiveHistoryStatsResponse(**stats)

    async def get_global_members_ranking(
        self, page: int = 1, limit: int = 20
    ) -> GlobalLiveMemberRankingResponse:
        skip = (page - 1) * limit
        ranking = await self.repository.get_global_live_members_ranking(skip, limit)
        total_count = await self.repository.get_total_global_live_members_count()
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
        self, member_id: str, page: int = 1, limit: int = 20
    ) -> GlobalLiveHistoryPaginationResponse:
        skip = (page - 1) * limit
        lives = await self.repository.get_global_history_by_member(
            member_id, skip, limit
        )
        total = await self.repository.get_total_global_history_count_by_member(
            member_id
        )
        total_pages = math.ceil(total / limit) if limit > 0 else 1

        return GlobalLiveHistoryPaginationResponse(
            data=lives, total=total, page=page, limit=limit, total_pages=total_pages
        )

    async def get_global_member_stats(
        self, member_id: str
    ) -> GlobalSingleMemberLiveHistoryStatsResponse:
        stats = await self.repository.get_global_member_stats(member_id)
        return GlobalSingleMemberLiveHistoryStatsResponse(**stats)
