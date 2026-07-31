import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from ..config import RecorderConfig
from ..models import RecordingSession


class QuotaExceededError(Exception):
    pass


class InvalidGrantError(Exception):
    pass


log = logging.getLogger("uploader")

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

_DAYS_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def _parse_wib_datetime(start_at: str) -> tuple[str, str]:
    if not start_at:
        return "", ""
    try:
        dt = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        wib_tz = timezone(timedelta(hours=7))
        dt = dt.astimezone(wib_tz)
        day_name = _DAYS_ID[dt.weekday()]
        date_str = f"{day_name}, {dt.day} {_MONTHS_ID[dt.month]} {dt.year}"
        time_str = dt.strftime("%H:%M")
        return date_str, time_str
    except (ValueError, AttributeError, KeyError):
        return "", ""


def _format_title(meta: dict) -> str:
    platform = (meta.get("platform") or "live").upper()
    nickname = meta.get("member_nickname") or meta.get("member_name") or "Unknown"
    date_str, time_str = _parse_wib_datetime(meta.get("start_at", ""))

    member_title = "JKT48" if nickname.upper() == "JKT48" else f"{nickname} JKT48"

    if date_str and time_str:
        return f"LIVE {platform} {member_title} | {date_str} {time_str} WIB"
    return f"LIVE {platform} {member_title}"


def _format_description(meta: dict) -> str:
    date_str, time_str = _parse_wib_datetime(meta.get("start_at", ""))
    full_name = meta.get("member_name", "")
    nickname = meta.get("member_nickname", "")

    if full_name.upper() == "JKT48" and (nickname.upper() == "JKT48" or not nickname):
        member_text = "JKT48"
        role_label = "Official"
    else:
        member_text = (
            f"{full_name} ({nickname}) JKT48" if nickname else f"{full_name} JKT48"
        )
        role_label = "Member"

    desc_lines = [
        f"Arsip siaran langsung dari platform {meta.get('platform', 'unknown').upper()}.",
        f"{role_label}: {member_text}",
    ]

    if date_str and time_str:
        desc_lines.append(f"Waktu Live: {date_str}, {time_str} WIB")

    desc_lines.extend(
        [
            "",
            "Terima kasih sudah menonton! Jangan lupa dukung terus JKT48 dan member kesayanganmu.",
            "",
        ]
    )

    hashtags = ["#ArsipJKT48"]

    nickname_clean = (nickname or "").replace(" ", "").replace("/", "_")
    if nickname_clean:
        if nickname_clean.upper() == "JKT48":
            hashtags.append("#JKT48")
        else:
            hashtags.append(f"#{nickname_clean}JKT48")

    desc_lines.append(" ".join(hashtags))

    return "\n".join(desc_lines)


def is_official_jkt48(meta: dict) -> bool:
    nickname = meta.get("member_nickname") or meta.get("member_name") or "Unknown"
    full_name = meta.get("member_name", "")
    return full_name.upper() == "JKT48" and (
        nickname.upper() == "JKT48" or not nickname
    )


def _get_privacy_status(meta: dict, default_status: str) -> str:
    live_type = meta.get("live_type", "public")
    if live_type != "public" and is_official_jkt48(meta):
        return "private"
    return "unlisted" if is_official_jkt48(meta) else default_status


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
    try:
        creds.refresh(Request())
    except Exception as e:
        if "invalid_grant" in str(e):
            raise InvalidGrantError() from e
        raise
    return build("youtube", "v3", credentials=creds)


def _do_upload_blocking(
    config: RecorderConfig,
    mp4_path: str,
    title: str,
    description: str,
    progress_callback=None,
    resume_uri: str | None = None,
    save_uri_callback=None,
    privacy_status: str | None = None,
) -> tuple[str | None, str | None]:
    youtube = _build_youtube(config)
    actual_privacy = privacy_status or config.youtube_privacy_status
    body = {
        "snippet": {
            "title": title,
            "description": description,
        },
        "status": {
            "privacyStatus": actual_privacy,
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
            if mp4_path:
                abort_path = os.path.join(os.path.dirname(mp4_path), ".abort_upload")
                if os.path.exists(abort_path):
                    raise Exception("Upload aborted: Live stream reconnected")

            status, response = request.next_chunk()
            if status and progress_callback:
                progress_callback(status.progress(), status.total_size)
            if save_uri_callback and not _uri_saved and request.resumable_uri:
                if request.resumable_uri != resume_uri:
                    save_uri_callback(request.resumable_uri)
                    _uri_saved = True
    except Exception as e:
        log.warning("YouTube upload failed: %s", e)
        if "Upload aborted" in str(e):
            raise
        is_quota = False
        try:
            if hasattr(e, "content") and e.content:
                body = json.loads(e.content)
                for err in body.get("error", {}).get("errors", []):
                    if err.get("reason") in (
                        "quotaExceeded",
                        "rateLimitExceeded",
                        "uploadLimitExceeded",
                    ):
                        is_quota = True
                        break
        except Exception:
            pass
        if (
            is_quota
            or "quotaExceeded" in str(e)
            or "rateLimitExceeded" in str(e)
            or "uploadLimitExceeded" in str(e)
        ):
            raise QuotaExceededError() from e
        if "invalid_grant" in str(e):
            raise InvalidGrantError() from e
        upload_uri = getattr(request, "resumable_uri", None) or resume_uri
        return None, upload_uri

    upload_uri = getattr(request, "resumable_uri", None) or resume_uri
    return response["id"], upload_uri


def _upload_thumbnail(
    config: RecorderConfig, youtube, video_id: str, thumbnail_path: str
):
    try:
        request = youtube.thumbnails().set(
            videoId=video_id, media_body=MediaFileUpload(thumbnail_path)
        )
        response = request.execute()
        log.info("Custom thumbnail uploaded successfully for %s", video_id)
        return True
    except Exception as e:
        log.warning("Failed to upload custom thumbnail for %s: %s", video_id, e)
        return False


def _add_to_playlist_blocking(
    config: RecorderConfig,
    video_id: str,
    meta: dict,
    privacy_status: str | None = None,
) -> None:
    youtube = _build_youtube(config)
    actual_privacy = privacy_status or config.youtube_privacy_status

    platform = (meta.get("platform") or "live").upper()
    nickname = meta.get("member_nickname") or meta.get("member_name") or "Unknown"

    full_name = meta.get("member_name", "")
    raw_nickname = meta.get("member_nickname", "")

    if full_name.upper() == "JKT48" and (
        raw_nickname.upper() == "JKT48" or not raw_nickname
    ):
        member_text = "JKT48"
    else:
        member_text = (
            f"{full_name} ({raw_nickname}) JKT48"
            if raw_nickname
            else f"{full_name} JKT48"
        )

    playlist_title = (
        f"JKT48 - Live {platform}"
        if nickname.upper() == "JKT48"
        else f"{nickname} JKT48 - Live {platform}"
    )

    live_type = meta.get("live_type", "public")
    if live_type != "public" and is_official_jkt48(meta):
        playlist_title = f"{playlist_title} - {live_type.upper()}"
        actual_privacy = "private"

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
                            "description": f"Kumpulan arsip siaran langsung {member_text} dari platform {platform}.",
                        },
                        "status": {"privacyStatus": actual_privacy},
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
    progress_callback=None,
    resume_uri: str | None = None,
    save_uri_callback=None,
) -> tuple[str | None, str | None]:
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

    # Check if a custom 16:9 thumbnail exists
    thumbnail_path = os.path.join(
        session.live_folder, f"{session.live_id}_yt_thumb.jpg"
    )
    if not os.path.exists(thumbnail_path):
        thumbnail_path = None

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
    description = _format_description(meta)

    privacy_status = _get_privacy_status(meta, config.youtube_privacy_status)

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
        privacy_status,
    )

    # Upload the custom thumbnail if generation was successful and video upload succeeded
    if youtube_id and thumbnail_path and os.path.exists(thumbnail_path):
        youtube = _build_youtube(config)
        _upload_thumbnail(config, youtube, youtube_id, thumbnail_path)

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
        privacy_status,
    )

    return youtube_id, upload_uri
