import asyncio
import io
import json
import logging
import os

import httpx

from ..config import RecorderConfig
from ..models import RecordingSession

log = logging.getLogger("uploader")

_REPLAY_API_TIMEOUT = 180
_MAX_UPLOAD_SIZE_BYTES = 52_428_800  # 50 MB


def _read_json_safe(path: str) -> dict | None:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _find_latest_screenshot(screenshot_dir: str) -> str | None:
    if not os.path.isdir(screenshot_dir):
        return None
    jpgs = [
        os.path.join(screenshot_dir, f)
        for f in os.listdir(screenshot_dir)
        if f.endswith(".jpg")
    ]
    if not jpgs:
        return None
    return max(jpgs, key=os.path.getmtime)


def _read_file(path: str) -> bytes | None:
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception:
        return None


def _get_dir_size(path: str) -> int:
    total_size = 0
    if not os.path.isdir(path):
        return total_size
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            if f.endswith((".mp4", ".ts", ".mkv")):
                continue
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size


async def upload(
    session: RecordingSession, config: RecorderConfig, title: str = ""
) -> bool:
    api_url = f"{config.api_base_url.rstrip('/')}{config.replay_api_url}"
    headers = {"Authorization": f"Bearer {config.api_key}"}
    if not api_url or not config.api_key:
        log.warning("replay_api_url or api_key not configured, skipping")
        return False

    metadata = _read_json_safe(session.json_path)
    if not metadata:
        log.error("Failed to read metadata: %s", session.json_path)
        return False

    if metadata.get("status") != "completed":
        log.warning(
            "Status is '%s', not 'completed'. Skipping upload.",
            metadata.get("status"),
        )
        return False

    live_id = session.live_id
    screenshot_dir = session.screenshots_folder

    live_folder_size = _get_dir_size(session.live_folder)
    if live_folder_size >= _MAX_UPLOAD_SIZE_BYTES:
        log.warning(
            "Folder size %s bytes exceeds 50MB limit. Skipping upload for %s",
            live_folder_size,
            title or live_id,
        )
        metadata["status"] = "tolarge"
        try:
            with open(session.json_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4)
        except Exception as e:
            log.error("Failed to update status to 'tolarge': %s", e)
        return False

    data = {"metadata": json.dumps(metadata), "force_update": "true"}

    for attempt in range(1, 4):
        files = []
        try:
            yt_thumb_path = os.path.join(session.live_folder, f"{live_id}_yt_thumb.jpg")
            if os.path.exists(yt_thumb_path):
                thumbnail_path = yt_thumb_path
            else:
                thumbnail_path = _find_latest_screenshot(screenshot_dir)
            if thumbnail_path:
                files.append(
                    (
                        "thumbnail",
                        (f"{live_id}.jpg", open(thumbnail_path, "rb"), "image/jpeg"),
                    )
                )

            if os.path.isdir(screenshot_dir):
                for fname in sorted(os.listdir(screenshot_dir)):
                    if fname.endswith(".jpg"):
                        fpath = os.path.join(screenshot_dir, fname)
                        files.append(
                            ("screenshots", (fname, open(fpath, "rb"), "image/jpeg"))
                        )

            jsonl_data = _read_file(session.jsonl_path) or b""
            srt_data = _read_file(session.srt_path) or b""
            files.append(
                (
                    "jsonl",
                    (
                        f"{live_id}.jsonl",
                        io.BytesIO(jsonl_data),
                        "application/x-ndjson",
                    ),
                )
            )
            files.append(
                ("srt", (f"{live_id}.srt", io.BytesIO(srt_data), "text/plain"))
            )

            async with httpx.AsyncClient(timeout=_REPLAY_API_TIMEOUT) as client:
                resp = await client.post(
                    api_url, data=data, files=files, headers=headers
                )
        except httpx.TimeoutException:
            log.warning("Timeout (attempt %d/3)", attempt)
            await asyncio.sleep(5)
            continue
        except httpx.RequestError as e:
            log.warning("Request failed (attempt %d/3): %s", attempt, e)
            await asyncio.sleep(5)
            continue
        finally:
            for _, fdata in files:
                try:
                    fdata[1].close()
                except Exception:
                    pass

        if resp.is_success:
            log.info("Replay data: %s → uploaded", title or live_id)
            return True
        else:
            body = resp.text[:500]
            log.warning(
                "Upload failed (attempt %d/3): %s %s", attempt, resp.status_code, body
            )
            if resp.status_code == 409:
                log.info(
                    "Replay data already exists (409). Treating as success for %s",
                    title or live_id,
                )
                return True
            await asyncio.sleep(5)

    log.error("All retries exhausted for %s", title or live_id)
    return False


async def update_youtube_metadata(
    live_id: str, youtube_id: str, youtube_title: str, config: RecorderConfig, log_upl
) -> bool:
    """Send a PATCH request to the backend to update YouTube data for a replay."""
    if not config.api_base_url or not config.api_key:
        log_upl.error("API base URL or API key not configured")
        return False

    api_url = f"{config.api_base_url.rstrip('/')}/admin/replay/{live_id}/youtube"
    headers = {"Authorization": f"Bearer {config.api_key}"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.patch(
                api_url,
                json={"youtube_id": youtube_id, "youtube_title": youtube_title},
                headers=headers,
            )
            if not resp.is_success:
                log_upl.error("Failed to patch YouTube ID: %s", resp.text)
                return False
            return True
    except Exception as e:
        log_upl.error("Error patching YouTube ID: %s", e)
        return False
