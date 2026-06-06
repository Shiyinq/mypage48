from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, BeforeValidator, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


class LiveHistoryUpdateRequest(BaseModel):
    live_id: str = Field(
        ..., description="Unique identifier for the live stream session"
    )
    member_id: str = Field(..., description="Identifier for the member streaming")
    member_name: str = Field(..., description="Name of the member")
    member_nickname: Optional[str] = Field(None, description="Nickname of the member")
    platform: str = Field(..., description="Platform of the live stream (showroom/idn)")
    ping_duration: int = Field(
        ..., ge=0, description="Duration to increment in seconds"
    )
    live_title: Optional[str] = Field(None, description="Title of the live stream")


class LiveHistoryResponse(BaseModel):
    id: str = Field(..., alias="_id")
    live_id: str
    member_id: str
    member_name: str
    member_nickname: Optional[str] = None
    platform: str
    live_title: Optional[str] = None
    duration: int = Field(..., description="Total watch duration in seconds")
    started_at: datetime
    last_updated_at: datetime


class LiveHistoryStatsResponse(BaseModel):
    total_duration: int
    total_watches: int
    top_member_id: Optional[str] = None
    top_member_name: Optional[str] = None
    top_member_watches: int = 0
    member_counts: dict[str, int]  # member_id -> watch count
    member_durations: dict[str, int]  # member_id -> total watch duration
    platform_counts: dict[str, int]  # platform -> watch count
    longest_watch: Optional["LongestWatchInfo"] = None


class LongestWatchInfo(BaseModel):
    duration: int
    live_title: Optional[str] = None
    platform: Optional[str] = None
    started_at: Optional[datetime] = None
    member_name: Optional[str] = None


class MemberLiveHistoryStatsResponse(BaseModel):
    member_id: str
    total_watches: int
    total_duration: int
    platform_counts: dict[str, int]
    longest_watch: Optional[LongestWatchInfo] = None


class GlobalSingleMemberLiveHistoryStatsResponse(BaseModel):
    member_id: str
    total_lives: int
    total_duration: int
    platform_counts: dict[str, int]
    longest_live: Optional[LongestWatchInfo] = None


class PaginationMeta(BaseModel):
    current_page: int
    last_page: int
    total_data: int
    per_page: int
    next_page: Optional[int] = None


class LiveHistoryPaginationResponse(BaseModel):
    data: List[LiveHistoryResponse]
    meta: PaginationMeta


class GlobalLiveHistory(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    live_id: str
    platform: str
    title: Optional[str] = None
    image: Optional[str] = None
    view_num: int = 0
    start_at: datetime
    end_at: Optional[datetime] = None
    last_seen_at: datetime
    status: str = "live"
    member: dict
    duration: int = 0


class GlobalLiveHistoryPaginationResponse(BaseModel):
    data: List[GlobalLiveHistory]
    total: int
    page: int
    limit: int
    total_pages: int


class WatchedLiveMemberRankingItem(BaseModel):
    member_id: str
    member_name: Optional[str] = None
    total_watches: int
    total_duration: int


class WatchedLiveMemberRankingResponse(BaseModel):
    data: List[WatchedLiveMemberRankingItem]
    meta: PaginationMeta


class GlobalLiveHistoryStatsResponse(BaseModel):
    total_lives: int
    total_duration: int
    unique_members_count: int
    top_member_id: Optional[str] = None
    top_member_name: Optional[str] = None
    top_member_watches: int = 0
    top_member_duration: int = 0
    platform_counts: dict[str, int]
    highest_view_live: Optional["LongestWatchInfo"] = None


class GlobalLiveMemberRankingItem(BaseModel):
    member_id: str
    member_name: Optional[str] = None
    total_watches: int
    total_duration: int


class GlobalLiveMemberRankingResponse(BaseModel):
    data: List[GlobalLiveMemberRankingItem]
    meta: PaginationMeta
