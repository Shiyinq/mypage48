from datetime import datetime
from typing import Annotated, Any, Optional

from fastapi import UploadFile
from pydantic import BaseModel, BeforeValidator, Field, field_serializer


def _serialize_dt(v: Optional[datetime]) -> Optional[str]:
    if v is None:
        return None
    return v.isoformat().replace("+00:00", "Z")


PyObjectId = Annotated[str, BeforeValidator(str)]


class ReplayUploadRequest(BaseModel):
    metadata: str = Field(..., description="JSON string of the info.json metadata")
    thumbnail: UploadFile = Field(..., description="Thumbnail image file (JPG)")
    jsonl: UploadFile = Field(..., description="Chat log file (JSONL)")
    srt: UploadFile = Field(..., description="Subtitle file (SRT)")
    screenshots: list[UploadFile] = Field(
        default_factory=list,
        description="Screenshot images from screenshots/ folder",
    )


class ReplayUpdateYouTube(BaseModel):
    youtube_id: str
    youtube_title: str


class ReplayFilesInfo(BaseModel):
    json_file: str
    thumbnail: Optional[str] = None
    jsonl: str
    srt: str
    screenshots: list[str]


class ReplayDetailFilesInfo(BaseModel):
    screenshots: list[str]


class ReplayResponse(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    live_id: str
    platform: str
    room_id: Optional[str] = None
    room_identifier: Optional[str] = None
    title: Optional[str] = None
    member_name: str
    member_nickname: str
    status: str
    start_at: Optional[datetime] = None
    recording_started_at: Optional[datetime] = None
    recording_ended_at: Optional[datetime] = None
    duration_seconds: int = 0
    srt_file: Optional[str] = None
    youtube_id: Optional[str] = None
    youtube_title: Optional[str] = None
    files: ReplayFilesInfo
    chats: list[dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime


class ReplayGiftSummary(BaseModel):
    name: str
    count: int
    total_gold: int
    image: Optional[str] = None
    free: Optional[bool] = None


class ReplayTopFan(BaseModel):
    user: str
    avatar: Optional[str] = None
    total_gold: int
    count: int
    free_gold: int = 0
    free_count: int = 0


class ReplayDetailResponse(BaseModel):
    id: PyObjectId = Field(..., alias="_id")
    live_id: str
    platform: str
    title: Optional[str] = None
    image: Optional[str] = None
    image_medium: Optional[str] = None
    image_small: Optional[str] = None
    blurHash: Optional[str] = None
    view_num: int = 0
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    status: str = "live"
    member: dict = {}
    duration: int = 0

    room_id: Optional[str] = None
    room_identifier: Optional[str] = None
    member_name: str
    member_nickname: str
    recording_started_at: Optional[datetime] = None
    recording_ended_at: Optional[datetime] = None
    duration_seconds: int = 0
    youtube_id: Optional[str] = None
    youtube_title: Optional[str] = None
    files: ReplayDetailFilesInfo
    total_chats: int = 0
    total_gifts: int = 0
    total_free_gifts: int = 0
    total_gold: int = 0
    total_loveletters: int = 0
    top_gifts: list[ReplayGiftSummary] = []
    top_fans: list[ReplayTopFan] = []
    created_at: datetime
    updated_at: datetime


class ReplayListItem(BaseModel):
    live_id: str = ""
    youtube_id: str = ""
    title: Optional[str] = None
    youtube_title: Optional[str] = None
    member: str = ""
    date: Optional[str] = None
    platform: str = ""
    added_at: Optional[datetime] = None
    duration: Optional[int] = None

    @field_serializer("added_at")
    def serialize_dt(self, v: Optional[datetime]) -> Optional[str]:
        return _serialize_dt(v)


class PaginationMeta(BaseModel):
    current_page: int
    last_page: int
    total_data: int
    per_page: int
    next_page: Optional[int] = None


class ReplayPaginationResponse(BaseModel):
    data: list[ReplayListItem]
    meta: PaginationMeta
