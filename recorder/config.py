from pathlib import Path

from pydantic_settings import BaseSettings


class RecorderConfig(BaseSettings):
    api_base_url: str = "http://localhost:8000/api"
    poll_interval: int = 10
    recordings_dir: str = str(Path(__file__).parent / "recordings" / "raw")
    max_recording_hours: int = 4
    showroom_comment_interval: float = 2.0
    log_level: str = "INFO"
    replay_api_url: str = "/admin/replay/upload"
    replay_api_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    youtube_refresh_token: str = ""

    model_config = {
        "env_file": (
            Path(__file__).parent.parent / ".env",
            Path(__file__).parent / ".env",
        ),
        "env_prefix": "REC_",
        "extra": "ignore",
    }
