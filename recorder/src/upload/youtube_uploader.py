import asyncio
import json
import os
from datetime import datetime
from logging import Logger

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from ..config import RecorderConfig
from ..models import RecordingSession

_MONTHS_ID = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


def _format_title(meta: dict) -> str:
    platform = (meta.get("platform") or "live").upper()
    nickname = meta.get("member_nickname") or meta.get("member_name") or "Unknown"
    start_at = meta.get("start_at", "")

    try:
        dt = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
        date_str = f"{dt.day} {_MONTHS_ID[dt.month]} {dt.year}"
        time_str = dt.strftime("%H:%M")
        return f"LIVE {platform} {nickname} JKT48 | {date_str} {time_str} WIB"
    except (ValueError, AttributeError, KeyError):
        return f"LIVE {platform} {nickname} JKT48"


def _build_youtube(config: RecorderConfig):
    creds = Credentials(
        None,
        refresh_token=config.youtube_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.google_client_id,
        client_secret=config.google_client_secret,
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def _do_upload_blocking(
    config: RecorderConfig,
    mp4_path: str,
    title: str,
    description: str,
    progress_callback=None,
) -> str:
    youtube = _build_youtube(config)
    body = {
        "snippet": {
            "title": title,
            "description": description,
        },
        "status": {
            "privacyStatus": config.youtube_privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(mp4_path, chunksize=256 * 1024, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status and progress_callback:
            progress_callback(status.progress(), status.total_size)

    return response["id"]


async def _upload_to_youtube(
    session: RecordingSession,
    config: RecorderConfig,
    log: Logger | None = None,
    progress_callback=None,
) -> str | None:
    if log is None:
        log = _get_fallback_logger()

    if (
        not config.google_client_id
        or not config.google_client_secret
        or not config.youtube_refresh_token
    ):
        return None

    meta_path = session.json_path
    if not os.path.exists(meta_path):
        log.warning("Metadata not found")
        return None

    with open(meta_path) as f:
        meta = json.load(f)

    if meta.get("youtube_id"):
        log.info("Already has youtube_id: %s, skipping", meta["youtube_id"])
        return meta["youtube_id"]

    mp4_path = None
    base = os.path.splitext(session.output_path)[0]
    for ext in [".mp4", ".mkv"]:
        p = base + ext
        if os.path.exists(p) and os.path.getsize(p) > 0:
            mp4_path = p
            break

    if not mp4_path:
        log.warning("No video file found")
        return None

    title = _format_title(meta)
    nickname_clean = (
        (meta.get("member_nickname") or "").replace(" ", "").replace("/", "_")
    )
    desc_lines = [
        f"Live recorded from {meta.get('platform', 'unknown').upper()}",
        f"Member: {meta.get('member_name', '')}",
    ]
    if nickname_clean:
        desc_lines.append(f"#{nickname_clean}JKT48")
    else:
        desc_lines.append("#JKT48")
    description = "\n".join(desc_lines)

    log.info("Uploading: %s", title)
    loop = asyncio.get_running_loop()
    youtube_id = await loop.run_in_executor(
        None,
        _do_upload_blocking,
        config,
        mp4_path,
        title,
        description,
        progress_callback,
    )

    meta["youtube_id"] = youtube_id
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    log.info("Uploaded: https://youtu.be/%s", youtube_id)
    return youtube_id


def _get_fallback_logger() -> Logger:
    import logging

    logger = logging.getLogger("uploader")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)
    return logger
