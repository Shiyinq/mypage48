import os
from pathlib import Path

from pydantic_settings import BaseSettings


class RecorderConfig(BaseSettings):
    api_base_url: str = "http://localhost:8000/api"
    poll_interval: int = 10
    recordings_dir: str = str(Path(__file__).parent / "recordings" / "raw")
    max_recording_hours: int = 4
    showroom_comment_interval: float = 2.0
    log_level: str = "INFO"

    model_config = {
        "env_file": os.path.join(Path(__file__).parent.parent, ".env"),
        "env_prefix": "REC_",
        "extra": "ignore",
    }
