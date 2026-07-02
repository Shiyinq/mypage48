import asyncio
import io
import json
import os

import httpx

from .config import RecorderConfig
from .models import RecordingSession

_REPLAY_API_TIMEOUT = 120


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


async def upload(session: RecordingSession, config: RecorderConfig) -> bool:
    api_url = f"{config.api_base_url.rstrip('/')}{config.replay_api_url}"
    api_key = config.replay_api_key
    if not api_url or not api_key:
        print("[uploader] replay_api_url or replay_api_key not configured, skipping")
        return False

    metadata = _read_json_safe(session.json_path)
    if not metadata:
        print(f"[uploader] Failed to read metadata: {session.json_path}")
        return False

    if metadata.get("status") != "completed":
        print(f"[uploader] Status is '{metadata.get('status')}', not 'completed'. Skipping upload.")
        return False

    live_id = session.live_id
    screenshot_dir = session.screenshots_folder

    data = {"metadata": json.dumps(metadata)}
    headers = {"Authorization": f"Bearer {api_key}"}

    for attempt in range(1, 4):
        files = []
        try:
            thumbnail_path = _find_latest_screenshot(screenshot_dir)
            if thumbnail_path:
                files.append(("thumbnail", (f"{live_id}.jpg", open(thumbnail_path, "rb"), "image/jpeg")))

            if os.path.isdir(screenshot_dir):
                for fname in sorted(os.listdir(screenshot_dir)):
                    if fname.endswith(".jpg"):
                        fpath = os.path.join(screenshot_dir, fname)
                        files.append(("screenshots", (fname, open(fpath, "rb"), "image/jpeg")))

            jsonl_data = _read_file(session.jsonl_path) or b""
            srt_data = _read_file(session.srt_path) or b""
            files.append(("jsonl", (f"{live_id}.jsonl", io.BytesIO(jsonl_data), "application/x-ndjson")))
            files.append(("srt", (f"{live_id}.srt", io.BytesIO(srt_data), "text/plain")))

            async with httpx.AsyncClient(timeout=_REPLAY_API_TIMEOUT) as client:
                resp = await client.post(api_url, data=data, files=files, headers=headers)
        except httpx.TimeoutException:
            print(f"[uploader] Timeout (attempt {attempt}/3)")
            await asyncio.sleep(5)
            continue
        except httpx.RequestError as e:
            print(f"[uploader] Request failed (attempt {attempt}/3): {e}")
            await asyncio.sleep(5)
            continue
        finally:
            for _, fdata in files:
                try:
                    fdata[1].close()
                except Exception:
                    pass

        if resp.is_success:
            print(f"[uploader] Replay uploaded: {live_id}")
            return True
        else:
            body = resp.text[:500]
            print(f"[uploader] Upload failed (attempt {attempt}/3): {resp.status_code} {body}")
            if resp.status_code == 409:
                return False
            await asyncio.sleep(5)

    print(f"[uploader] All retries exhausted for {live_id}")
    return False


async def upload_existing(config: RecorderConfig):
    """Scan raw recordings dir and upload any completed sessions in parallel."""
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
        print(f"[uploader] Processing {len(tasks)} existing completed session(s)...")
        await asyncio.gather(*tasks, return_exceptions=True)
