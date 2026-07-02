import asyncio
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LiveInfo:
    live_id: str
    platform: str
    member_name: str
    member_nickname: str
    room_id: str
    room_identifier: Optional[str] = None
    hls_url: Optional[str] = None
    title: str = ""
    member_image: str = ""
    start_at: str = ""


@dataclass
class RecordingSession:
    live_id: str
    platform: str
    member_name: str
    member_nickname: str
    room_id: str
    room_identifier: Optional[str]
    hls_url: str
    recording_start_time: float
    output_path: str
    chat_log_path: str
    srt_path: str
    json_path: str
    jsonl_path: str
    thumbnail_path: str
    screenshots_folder: str
    live_folder: str
    title: str
    member_image: str
    start_at: str
    ffmpeg_proc: Optional[subprocess.Popen] = None
    chat_task: Optional["asyncio.Task"] = None
    started_at: float = field(default_factory=time.time)
