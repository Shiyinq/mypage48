import asyncio
import json
import os
import shutil
import time
from datetime import datetime, timezone
from logging import Logger

from . import r2_uploader
from .config import RecorderConfig
from .models import RecordingSession
from .youtube_uploader import _upload_to_youtube


class Watcher:
    def __init__(self, config: RecorderConfig, log_rec: Logger, log_upl: Logger):
        self.config = config
        self.log_rec = log_rec
        self.log_upl = log_upl
        self._processing: dict[str, dict] = {}

    async def run(self, stop_event: asyncio.Event):
        os.makedirs(self.config.logs_dir, exist_ok=True)

        while not stop_event.is_set():
            try:
                await self._process_loop()
            except Exception as e:
                self.log_rec.error("Loop error: %s", e)

            try:
                await asyncio.wait_for(
                    stop_event.wait(), timeout=self.config.poll_interval
                )
                break
            except asyncio.TimeoutError:
                pass

    async def _process_loop(self):
        raw_dir = self.config.recordings_dir
        if not os.path.isdir(raw_dir):
            return

        done = self._read_history()
        tasks = []

        for entry in sorted(os.listdir(raw_dir)):
            folder_path = os.path.join(raw_dir, entry)
            if not os.path.isdir(folder_path):
                continue

            meta = self._read_meta(folder_path)
            if not meta or meta.get("status") != "completed":
                continue

            live_id = meta.get("live_id")
            if not live_id:
                continue

            if live_id in done:
                self.log_rec.info("Skipping %s (already in uploads history)", live_id)
                continue

            if live_id in self._processing:
                info = self._processing[live_id]
                elapsed = int(time.time() - info.get("started_at", time.time()))
                phase = info.get("phase", "?")
                pct = info.get("pct")
                if pct is not None:
                    self.log_rec.info(
                        "Already processing %s (%s, %d%%, %ds elapsed)",
                        live_id,
                        phase,
                        pct,
                        elapsed,
                    )
                else:
                    self.log_rec.info(
                        "Already processing %s (%s, %ds elapsed)",
                        live_id,
                        phase,
                        elapsed,
                    )
                continue

            self._processing[live_id] = {"started_at": time.time(), "phase": "pending"}
            tasks.append(self._process_folder(folder_path, live_id))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_folder(self, folder_path: str, live_id: str):
        try:
            await self._process_folder_inner(folder_path, live_id)
        finally:
            self._processing.pop(live_id, None)

    async def _process_folder_inner(self, folder_path: str, live_id: str):
        meta, session = self._build_session(folder_path, live_id)
        if not meta or not session:
            return

        youtube_id = meta.get("youtube_id")

        mp4_path = os.path.join(folder_path, f"{live_id}.mp4")
        has_mp4 = os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 0
        yt_configured = all(
            [
                self.config.google_client_id,
                self.config.google_client_secret,
                self.config.youtube_refresh_token,
            ]
        )

        if has_mp4:
            if not yt_configured:
                self.log_rec.info(
                    "YouTube not configured, keeping folder for %s", live_id
                )
                return

            try:
                self._processing[live_id]["phase"] = "uploading to YouTube"

                def _on_progress(done_bytes, total_bytes):
                    pct = int(done_bytes * 100 / total_bytes) if total_bytes else 0
                    self._processing[live_id]["pct"] = pct

                ytid = await _upload_to_youtube(
                    session,
                    self.config,
                    self.log_upl,
                    progress_callback=_on_progress,
                )
                if ytid:
                    youtube_id = ytid
                    os.remove(mp4_path)
                else:
                    self.log_upl.warning(
                        "YouTube upload failed for %s, will retry", live_id
                    )
                    return
            except Exception as e:
                self.log_upl.error("YouTube upload failed for %s: %s", live_id, e)
                return
        else:
            self.log_rec.info("No mp4 for %s, skipping YouTube", live_id)

        self._processing[live_id]["phase"] = "uploading to R2"
        self._processing[live_id].pop("pct", None)

        ok = await r2_uploader.upload(session, self.config, self.log_upl)
        if not ok:
            self.log_upl.warning("R2 upload failed for %s, will retry", live_id)
            return

        self._append_history(live_id, youtube_id or "")
        shutil.rmtree(folder_path)
        self.log_rec.info("Done: %s", live_id)

    def _read_history(self) -> set[str]:
        path = self.config.uploads_history_path
        if not os.path.exists(path):
            return set()
        done = set()
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            if data.get("live_id"):
                                done.add(data["live_id"])
                        except json.JSONDecodeError:
                            pass
        except Exception:
            pass
        return done

    def _append_history(self, live_id: str, youtube_id: str):
        path = self.config.uploads_history_path
        try:
            with open(path, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "live_id": live_id,
                            "youtube_id": youtube_id,
                            "uploaded_at": datetime.now(timezone.utc).strftime(
                                "%Y-%m-%dT%H:%M:%SZ"
                            ),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except Exception as e:
            self.log_rec.error("Failed to write history: %s", e)

    @staticmethod
    def _read_meta(folder_path: str) -> dict | None:
        for f in os.listdir(folder_path):
            if f.endswith(".json") and not f.endswith(".jsonl"):
                try:
                    with open(os.path.join(folder_path, f)) as fh:
                        return json.load(fh)
                except Exception:
                    return None
        return None

    @staticmethod
    def _build_session(
        folder_path: str, live_id: str
    ) -> tuple[dict | None, RecordingSession | None]:
        meta = None
        json_file = jsonl_file = srt_file = None
        for f in os.listdir(folder_path):
            if f.endswith(".json") and not f.endswith(".jsonl"):
                json_file = f
            elif f.endswith(".jsonl"):
                jsonl_file = f
            elif f.endswith(".srt"):
                srt_file = f

        if not json_file:
            return None, None

        meta_path = os.path.join(folder_path, json_file)
        try:
            with open(meta_path) as f:
                meta = json.load(f)
        except Exception:
            return None, None

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

        return meta, session
