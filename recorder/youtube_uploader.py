import asyncio
import json
import os
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from . import uploader
from .config import RecorderConfig
from .models import RecordingSession

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
    config: RecorderConfig, mp4_path: str, title: str, description: str
) -> str:
    youtube = _build_youtube(config)
    body = {
        "snippet": {
            "title": title,
            "description": description,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(mp4_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )
    response = request.execute()
    return response["id"]


async def _upload_to_youtube(
    session: RecordingSession, config: RecorderConfig
) -> str | None:
    if (
        not config.google_client_id
        or not config.google_client_secret
        or not config.youtube_refresh_token
    ):
        return None

    meta_path = session.json_path
    if not os.path.exists(meta_path):
        print("[youtube] Metadata not found")
        return None

    with open(meta_path) as f:
        meta = json.load(f)

    if meta.get("youtube_id"):
        print(f"[youtube] Already has youtube_id: {meta['youtube_id']}, skipping")
        return meta["youtube_id"]

    mp4_path = None
    base = os.path.splitext(session.output_path)[0]
    for ext in [".mp4", ".mkv"]:
        p = base + ext
        if os.path.exists(p) and os.path.getsize(p) > 0:
            mp4_path = p
            break

    if not mp4_path:
        print("[youtube] No video file found")
        return None

    title = _format_title(meta)
    description = (
        f"Live recorded from {meta.get('platform', 'unknown').upper()}\n"
        f"Member: {meta.get('member_name', '')}\n"
        "#JKT48"
    )

    print(f"[youtube] Uploading: {title}")
    loop = asyncio.get_running_loop()
    youtube_id = await loop.run_in_executor(
        None, _do_upload_blocking, config, mp4_path, title, description
    )

    meta["youtube_id"] = youtube_id
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(f"[youtube] Uploaded: https://youtu.be/{youtube_id}")
    return youtube_id


async def upload(session: RecordingSession, config: RecorderConfig):
    await _upload_to_youtube(session, config)
    await uploader.upload(session, config)


def _read_json_safe(path: str) -> dict | None:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


async def upload_existing(config: RecorderConfig):
    raw_dir = config.recordings_dir
    if not os.path.isdir(raw_dir):
        return

    tasks = []
    for entry in sorted(os.listdir(raw_dir)):
        folder_path = os.path.join(raw_dir, entry)
        if not os.path.isdir(folder_path):
            continue

        json_file = jsonl_file = srt_file = None
        for f in os.listdir(folder_path):
            if f.endswith(".json") and not f.endswith(".jsonl"):
                json_file = f
            elif f.endswith(".jsonl"):
                jsonl_file = f
            elif f.endswith(".srt"):
                srt_file = f

        if not json_file:
            continue

        meta_path = os.path.join(folder_path, json_file)
        meta = _read_json_safe(meta_path)
        if not meta or meta.get("status") != "completed":
            continue

        live_id = meta.get("live_id", json_file.replace(".json", ""))

        session = RecordingSession(
            live_id=live_id,
            platform=meta.get("platform", ""),
            member_name=meta.get("member_name", ""),
            member_nickname=meta.get("member_nickname", ""),
            room_id=meta.get("room_id", ""),
            room_identifier=meta.get("room_identifier"),
            hls_url="",
            recording_start_time=0.0,
            output_path=os.path.join(folder_path, f"{live_id}.mp4"),
            chat_log_path=os.path.join(folder_path, f"{live_id}.txt"),
            srt_path=os.path.join(folder_path, srt_file) if srt_file else "",
            json_path=meta_path,
            jsonl_path=os.path.join(folder_path, jsonl_file) if jsonl_file else "",
            thumbnail_path="",
            screenshots_folder=os.path.join(folder_path, "screenshots"),
            live_folder=folder_path,
            title=meta.get("title", ""),
            member_image="",
            start_at=meta.get("start_at", ""),
        )

        tasks.append(upload(session, config))

    if tasks:
        print(f"[youtube] Processing {len(tasks)} existing completed session(s)...")
        await asyncio.gather(*tasks, return_exceptions=True)
