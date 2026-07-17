from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class LiveMember(BaseModel):
    id: str
    name: str
    nickname: Optional[str] = None
    img: Optional[str] = None


class LiveStreamingURL(BaseModel):
    url: str
    label: str
    quality: int


class LiveStreamInfo(BaseModel):
    streaming_urls: List[LiveStreamingURL]
    room_identifier: Optional[str] = None
    view_num: int = 0
    start_at: Optional[datetime] = None
    image: Optional[str] = None
    member: Optional[LiveMember] = None
    live_type: str = "public"
    live_id: Optional[str] = None
    room_url_key: Optional[str] = None


class LiveStatus(BaseModel):
    platform: str  # 'showroom' or 'idn'
    room_id: Optional[str] = None
    room_identifier: Optional[str] = None
    room_url_key: Optional[str] = None
    live_id: Optional[str] = None
    title: Optional[str] = None
    view_num: int = 0
    start_at: Optional[datetime] = None
    image: Optional[str] = None
    streaming_url: List[LiveStreamingURL] = []
    member: Optional[LiveMember] = None
    live_type: str = "public"
    streamer_uuid: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    record: bool = True


class LiveResponse(BaseModel):
    data: List[LiveStatus]
    total: int
    updated_at: datetime
