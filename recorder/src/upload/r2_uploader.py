import asyncio
import io
import json
import os
from logging import Logger

import httpx

from ..config import RecorderConfig
from ..models import RecordingSession

_REPLAY_API_TIMEOUT = 180


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


async def upload(
    session: RecordingSession, config: RecorderConfig, log: Logger, title: str = ""
) -> bool:
    api_url = f"{config.api_base_url.rstrip('/')}{config.replay_api_url}"
    api_key = config.replay_api_key
    if not api_url or not api_key:
        log.warning("replay_api_url or replay_api_key not configured, skipping")
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

    data = {"metadata": json.dumps(metadata)}
    headers = {"Authorization": f"Bearer {api_key}"}

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
