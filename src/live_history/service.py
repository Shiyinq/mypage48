import asyncio
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
    PCLiveHistoryPaginationResponse,
    WatchedLiveMemberRankingResponse,
)
from src.storage.service import StorageService
from src.utils import parse_date_range


class LiveHistoryService:
    def __init__(
        self, repository: LiveHistoryRepository, storage_service: StorageService
    ):
        self.repository = repository
        self.storage_service = storage_service

    async def get_global_history(
        self,
        page: int = 1,
        limit: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> GlobalLiveHistoryPaginationResponse:
        skip = (page - 1) * limit
        parsed_start, parsed_end = parse_date_range(start_date, end_date)
        lives = await self.repository.get_global_history(
            skip=skip, limit=limit, start_date=parsed_start, end_date=parsed_end
        )
        total = await self.repository.get_total_global_history_count(
            start_date=parsed_start, end_date=parsed_end
        )
        total_pages = math.ceil(total / limit) if limit > 0 else 1

        async def resolve_variants(d: dict):
            if d.get("image") and d["image"].startswith("live/"):
                variants = await self.storage_service.resolve_image_variants(d["image"])
                d["image"] = variants.get("url")
                d["image_medium"] = variants.get("url_medium")
                d["image_small"] = variants.get("url_small")
                if variants.get("blurHash") and not d.get("blurHash"):
                    d["blurHash"] = variants.get("blurHash")

        await asyncio.gather(*(resolve_variants(d) for d in lives))

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

        parsed_start, parsed_end = parse_date_range(start_date, end_date)

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
        parsed_start, parsed_end = parse_date_range(start_date, end_date)
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
        parsed_start, parsed_end = parse_date_range(start_date, end_date)
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
        parsed_start, parsed_end = parse_date_range(start_date, end_date)
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

    async def get_global_stats(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> GlobalLiveHistoryStatsResponse:
        parsed_start, parsed_end = parse_date_range(start_date, end_date)
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
        parsed_start, parsed_end = parse_date_range(start_date, end_date)
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
        parsed_start, parsed_end = parse_date_range(start_date, end_date)
        lives = await self.repository.get_global_history_by_member(
            member_id, skip, limit, start_date=parsed_start, end_date=parsed_end
        )
        total = await self.repository.get_total_global_history_count_by_member(
            member_id, start_date=parsed_start, end_date=parsed_end
        )
        total_pages = math.ceil(total / limit) if limit > 0 else 1

        async def resolve_variants(d: dict):
            if d.get("image") and d["image"].startswith("live/"):
                variants = await self.storage_service.resolve_image_variants(d["image"])
                d["image"] = variants.get("url")
                d["image_medium"] = variants.get("url_medium")
                d["image_small"] = variants.get("url_small")
                if variants.get("blurHash") and not d.get("blurHash"):
                    d["blurHash"] = variants.get("blurHash")

        await asyncio.gather(*(resolve_variants(d) for d in lives))

        return GlobalLiveHistoryPaginationResponse(
            data=lives, total=total, page=page, limit=limit, total_pages=total_pages
        )

    async def get_global_member_stats(
        self,
        member_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> GlobalSingleMemberLiveHistoryStatsResponse:
        parsed_start, parsed_end = parse_date_range(start_date, end_date)
        stats = await self.repository.get_global_member_stats(
            member_id, start_date=parsed_start, end_date=parsed_end
        )
        return GlobalSingleMemberLiveHistoryStatsResponse(**stats)

    async def get_pc_collection(
        self,
        user_id: Optional[str],
        collection_type: str = "all",
        page: int = 1,
        limit: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort_by: str = "date_desc",
    ) -> PCLiveHistoryPaginationResponse:
        parsed_start, parsed_end = parse_date_range(start_date, end_date)
        skip = (page - 1) * limit

        items = await self.repository.get_pc_collection(
            user_id=user_id,
            collection_type=collection_type,
            skip=skip,
            limit=limit,
            start_date=parsed_start,
            end_date=parsed_end,
            sort_by=sort_by,
        )
        total = await self.repository.get_total_pc_collection_count(
            user_id, collection_type, start_date=parsed_start, end_date=parsed_end
        )
        total_pages = math.ceil(total / limit) if limit > 0 else 1

        async def resolve_variants(d: dict):
            if d.get("image") and d["image"].startswith("live/"):
                variants = await self.storage_service.resolve_image_variants(d["image"])
                d["image"] = variants.get("url")
                d["image_medium"] = variants.get("url_medium")
                d["image_small"] = variants.get("url_small")
                if variants.get("blurHash") and not d.get("blurHash"):
                    d["blurHash"] = variants.get("blurHash")

        await asyncio.gather(*(resolve_variants(d) for d in items))

        return PCLiveHistoryPaginationResponse(
            data=items, total=total, page=page, limit=limit, total_pages=total_pages
        )
