import math
from typing import Any, Dict, Optional

from src.live_history.exceptions import LiveHistoryUpdateError
from src.live_history.repository import LiveHistoryRepository
from src.live_history.schemas import (
    LiveHistoryResponse,
    LiveHistoryStatsResponse,
    LiveHistoryUpdateRequest,
    MemberLiveHistoryStatsResponse,
)


class LiveHistoryService:
    def __init__(self, repository: LiveHistoryRepository):
        self.repository = repository

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
