import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
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
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        wib_tz = timezone(timedelta(hours=7))
        dt = dt.astimezone(wib_tz)
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
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
        ],
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def _do_upload_blocking(
    config: RecorderConfig,
    mp4_path: str,
    title: str,
    description: str,
    progress_callback=None,
    resume_uri: str | None = None,
    save_uri_callback=None,
) -> tuple[str | None, str | None]:
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
    if resume_uri:
        request.resumable_uri = resume_uri

    response = None
    _uri_saved = bool(resume_uri)
    try:
        while response is None:
            status, response = request.next_chunk()
            if status and progress_callback:
                progress_callback(status.progress(), status.total_size)
            if save_uri_callback and not _uri_saved and request.resumable_uri:
                if request.resumable_uri != resume_uri:
                    save_uri_callback(request.resumable_uri)
                    _uri_saved = True
    except Exception:
        upload_uri = getattr(request, "resumable_uri", None) or resume_uri
        return None, upload_uri

    upload_uri = getattr(request, "resumable_uri", None) or resume_uri
    return response["id"], upload_uri


def _add_to_playlist_blocking(
    config: RecorderConfig, video_id: str, meta: dict, log: Logger
) -> None:
    youtube = _build_youtube(config)

    platform = (meta.get("platform") or "live").upper()
    nickname = meta.get("member_nickname") or meta.get("member_name") or "Unknown"

    playlist_title = f"{nickname} JKT48 - Live {platform}"

    try:
        request = youtube.playlists().list(part="snippet", mine=True, maxResults=50)
        playlist_id = None
        while request is not None:
            response = request.execute()
            for item in response.get("items", []):
                if item["snippet"]["title"] == playlist_title:
                    playlist_id = item["id"]
                    break
            if playlist_id:
                break
            request = youtube.playlists().list_next(request, response)

        if not playlist_id:
            log.info("Creating playlist: %s", playlist_title)
            playlist_response = (
                youtube.playlists()
                .insert(
                    part="snippet,status",
                    body={
                        "snippet": {
                            "title": playlist_title,
                            "description": f"Live recordings of {nickname} JKT48 on {platform}",
                        },
                        "status": {"privacyStatus": config.youtube_privacy_status},
                    },
                )
                .execute()
            )
            playlist_id = playlist_response["id"]

        log.info("Adding video %s to playlist %s", video_id, playlist_title)
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id},
                }
            },
        ).execute()
    except Exception as e:
        log.error("Failed to add video to playlist: %s", e)


async def _upload_to_youtube(
    session: RecordingSession,
    config: RecorderConfig,
    log: Logger | None = None,
    progress_callback=None,
    resume_uri: str | None = None,
    save_uri_callback=None,
) -> tuple[str | None, str | None]:
    if log is None:
        log = _get_fallback_logger()

    if (
        not config.google_client_id
        or not config.google_client_secret
        or not config.youtube_refresh_token
    ):
        return None, None

    meta_path = session.json_path
    if not os.path.exists(meta_path):
        log.warning("Metadata not found")
        return None, None

    with open(meta_path) as f:
        meta = json.load(f)

    if meta.get("youtube_id"):
        log.info("Already has youtube_id: %s, skipping", meta["youtube_id"])
        return meta["youtube_id"], None

    mp4_path = None
    base = os.path.splitext(session.output_path)[0]
    for ext in [".mp4", ".mkv"]:
        p = base + ext
        if os.path.exists(p) and os.path.getsize(p) > 0:
            mp4_path = p
            break

    if not mp4_path:
        log.warning("No video file found")
        return None, None

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
    if resume_uri:
        log.info("Resuming upload for %s with saved URI", title)
    loop = asyncio.get_running_loop()
    youtube_id, upload_uri = await loop.run_in_executor(
        None,
        _do_upload_blocking,
        config,
        mp4_path,
        title,
        description,
        progress_callback,
        resume_uri,
        save_uri_callback,
    )

    if not youtube_id:
        return None, upload_uri

    meta["youtube_id"] = youtube_id
    meta["youtube_title"] = title
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    log.info("Video: %s → https://youtu.be/%s", title, youtube_id)

    # Add to playlist
    await loop.run_in_executor(
        None,
        _add_to_playlist_blocking,
        config,
        youtube_id,
        meta,
        log,
    )

    return youtube_id, upload_uri


def _get_fallback_logger() -> Logger:
    import logging

    logger = logging.getLogger("uploader")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.INFO)
    return logger
