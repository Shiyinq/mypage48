import os
import re
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class RecorderConfig(BaseSettings):
    api_base_url: str = "http://localhost:8000/api"
    frontend_base_url: str = "http://localhost:5173"
    poll_interval: int = 3
    news_check_interval: int = 300
    schedule_check_interval: int = 300
    health_check_interval: int = 300
    heartbeat_interval: int = 120
    env: str = "dev"
    enable_flaresolverr: bool = False
    flaresolverr_url: str = "http://localhost:8191/v1"
    recordings_dir: str = str(Path(__file__).parent.parent / "recordings")
    theater_dir: str = str(Path(__file__).parent.parent / "theater")
    max_recording_hours: int = 4
    showroom_comment_interval: float = 2.0
    showroom_gift_interval: float = 5.0
    log_level: str = "INFO"
    log_mode: str = "stdout"
    logs_dir: str = str(Path(__file__).parent.parent / "logs")
    replay_api_url: str = "/admin/replay/upload"
    api_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    youtube_refresh_token: str = ""
    backup_to_gdrive: bool = False
    gdrive_to_youtube: bool = False
    gdrive_max_concurrent_uploads: int = 1
    gdrive_refresh_token: str = ""
    gdrive_delete_after_youtube_upload: bool = False
    gdrive_keep_members: str = ""
    youtube_privacy_status: str = "unlisted"
    telegram_enabled: bool = True
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    page48_enabled: bool = False
    page48_api_key: str = ""
    page48_base_url: str = ""
    remux_timeout: int = 600
    max_concurrent_uploads: int = 2
    enable_upload_queue: bool = True
    youtube_upload_delay_minutes: int = 30
    youtube_upload_priority: str = ""

    ytpublic_enabled: bool = False
    ytpublic_dry_run: bool = True
    ytpublic_poll_interval: int = Field(default=900, ge=60)
    ytpublic_base_delay_hours: int = Field(default=72, ge=72)
    ytpublic_buffer_hours: int = Field(default=8, ge=0)
    ytpublic_exclude_video_ids: str = ""
    ytpublic_max_updates_per_day: int = Field(default=80, gt=0)
    ytpublic_max_updates_per_scan: int = Field(default=5, gt=0)
    ytpublic_update_interval_seconds: int = Field(default=30, ge=0)
    ytpublic_daily_quota_budget: int = Field(default=5000, ge=51)

    @property
    def ytpublic_excluded_video_ids(self) -> set[str]:
        video_ids = {
            value.strip()
            for value in self.ytpublic_exclude_video_ids.split(",")
            if value.strip()
        }
        if any(
            re.fullmatch(r"[A-Za-z0-9_-]{11}", value) is None for value in video_ids
        ):
            raise ValueError(
                "ytpublic excluded video IDs must be 11-character YouTube IDs"
            )
        return video_ids

    @property
    def gdrive_keep_members_normalized(self) -> set[str]:
        return {
            nickname.strip().casefold()
            for nickname in self.gdrive_keep_members.split(",")
            if nickname.strip()
        }

    @property
    def youtube_upload_priority_ranks(self) -> dict[str, int]:
        ranks = {}
        for nickname in self.youtube_upload_priority.split(","):
            nickname = nickname.strip().casefold()
            if nickname and nickname not in ranks:
                ranks[nickname] = len(ranks)
        return ranks

    model_config = {
        "env_file": (
            Path(__file__).parent.parent / ".env",
            Path(__file__).parent / ".env",
        ),
        "env_prefix": "REC_",
        "extra": "ignore",
    }

    @property
    def uploads_history_path(self) -> str:
        return os.path.join(self.logs_dir, "uploads.jsonl")

    @property
    def page48_api_base_url(self) -> str:
        """Base URL for Page48 posting; falls back to the main API base URL."""
        base = self.page48_base_url or self.api_base_url
        return base.rstrip("/")
