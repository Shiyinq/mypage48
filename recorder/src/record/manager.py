import asyncio
import glob
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

from ..config import RecorderConfig
from ..models import LiveInfo, RecordingSession
from ..notify import telegram_notifier
from . import chat_capture, srt_generator, stream_recorder
from .live_detector import LiveDetector


def _parse_start_at(start_at: str) -> int:
    if not start_at:
        return int(time.time())
    try:
        dt = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        return int(time.time())


def _get_duration(mp4_path: str) -> float:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                mp4_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    return 0.0


def _sanitize_filename(name: str) -> str:
    return re.sub(r"[^\w\s\-]", "_", name).strip().lower()


class RecordingManager:
    def __init__(self, config: RecorderConfig):
        self.config = config
        self.log = logging.getLogger("recorder")
        self.detector = LiveDetector(config)
        self.sessions: dict[str, RecordingSession] = {}
        self._stop_events: dict[str, asyncio.Event] = {}
        self._gone_count: dict[str, int] = {}
        self._pending_ends: set[str] = set()

    async def sync(self, current_lives: list[LiveInfo]):
        current_ids = {l.live_id for l in current_lives}

        for live in current_lives:
            if live.live_id not in self.sessions:
                await self._start_session(live)

        ended_ids = set(self.sessions.keys()) - current_ids - self._pending_ends
        for live_id in ended_ids:
            count = self._gone_count.get(live_id, 0) + 1
            self._gone_count[live_id] = count
            if count >= 3:
                session = self.sessions.get(live_id)
                if session:
                    stream_info, is_not_found = await self.detector.get_streaming_url(
                        session.platform, session.room_id, session.live_id
                    )
                    if stream_info:
                        self.log.warning(
                            "Live %s disappeared from poll but stream URL still active, "
                            "resetting gone count",
                            live_id,
                        )
                        self._gone_count[live_id] = 0
                        continue
                    if not is_not_found:
                        self.log.warning(
                            "Live %s gone from poll but streaming URL check failed "
                            "(not 404), keeping session",
                            live_id,
                        )
                        self._gone_count[live_id] = 0
                        continue
                del self._gone_count[live_id]
                asyncio.create_task(self._end_session(live_id, reason="completed"))

        for live_id in current_ids:
            self._gone_count.pop(live_id, None)

    def _restart_ffmpeg(self, session: RecordingSession, stream_info: dict):
        if session.ffmpeg_proc and stream_recorder.is_running(session.ffmpeg_proc):
            stream_recorder.stop(session.ffmpeg_proc)

        part_idx = len(session.mkv_parts) + 1
        old_mkv = session.output_path
        new_mkv = old_mkv.replace(".mkv", f"_part{part_idx}.mkv")
        if os.path.exists(old_mkv):
            if os.path.getsize(old_mkv) > 1024:
                try:
                    os.rename(old_mkv, new_mkv)
                    session.mkv_parts.append(new_mkv)

                    # Update JSON safely so we don't lose track of parts if it crashes
                    try:
                        with open(session.json_path, "r") as f:
                            data = json.load(f)
                        data["mkv_parts"] = session.mkv_parts
                        with open(session.json_path, "w") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        self.log.warning("Failed to update JSON after restart: %s", e)

                except Exception as e:
                    self.log.error("Failed to rename mkv part: %s", e)
            else:
                try:
                    os.remove(old_mkv)
                except Exception:
                    pass

        new_hls_url = self.detector.pick_best_url(stream_info) or session.hls_url
        session.hls_url = new_hls_url
        session.ffmpeg_proc = stream_recorder.start(
            new_hls_url, old_mkv, headers=self._get_platform_headers(session)
        )

    async def check_health(self):
        completed_ids = []
        error_ids = []
        now = time.time()
        for live_id, session in self.sessions.items():
            if live_id in self._pending_ends:
                continue

            if session.ffmpeg_proc and not stream_recorder.is_running(
                session.ffmpeg_proc
            ):
                self.log.warning("ffmpeg died for %s", live_id)
                stream_info, is_not_found = await self.detector.get_streaming_url(
                    session.platform, session.room_id, session.live_id
                )
                if stream_info:
                    self.log.warning(
                        "Stream still live, restarting ffmpeg for %s", live_id
                    )
                    self._restart_ffmpeg(session, stream_info)
                elif is_not_found:
                    self.log.info("Stream ended, marking completed for %s", live_id)
                    completed_ids.append(live_id)
                else:
                    self.log.warning("Failed to get streaming URL for %s", live_id)
                continue
            if os.path.exists(session.output_path):
                current_size = os.path.getsize(session.output_path)
                age = now - os.path.getmtime(session.output_path)

                if age > 300 and current_size == session.last_file_size:
                    self.log.warning(
                        "ffmpeg stalled for %s (age: %.0fs, size unchanged: %s)",
                        live_id,
                        age,
                        current_size,
                    )
                    stream_info, is_not_found = await self.detector.get_streaming_url(
                        session.platform, session.room_id, session.live_id
                    )
                    if stream_info:
                        self.log.warning(
                            "Stream still live, restarting stalled ffmpeg for %s",
                            live_id,
                        )
                        self._restart_ffmpeg(session, stream_info)
                    elif is_not_found:
                        completed_ids.append(live_id)
                    else:
                        self.log.warning(
                            "Failed to get streaming URL for %s, keeping session",
                            live_id,
                        )

                session.last_file_size = current_size

        for live_id in completed_ids:
            asyncio.create_task(self._end_session(live_id, reason="completed"))
        for live_id in error_ids:
            asyncio.create_task(self._end_session(live_id, reason="error"))

    def log_progress(self):
        if not self.sessions:
            return

        self.log.info("Recording Progress:")
        for live_id, session in self.sessions.items():
            elapsed = time.time() - session.recording_start_time
            duration_str = self._format_duration(elapsed)

            file_size = 0
            if os.path.exists(session.output_path):
                file_size = os.path.getsize(session.output_path)

            chat_count = 0
            if os.path.exists(session.chat_log_path):
                try:
                    with open(session.chat_log_path) as f:
                        chat_count = sum(1 for _ in f)
                except Exception:
                    pass

            screenshot_count = 0
            if os.path.exists(session.screenshots_folder):
                try:
                    screenshot_count = len(
                        [
                            f
                            for f in os.listdir(session.screenshots_folder)
                            if f.endswith(".jpg")
                        ]
                    )
                except Exception:
                    pass

            self.log.info(
                "  %s (%s) | %s | %s | %s chats | %s screenshots",
                session.member_nickname,
                session.platform,
                duration_str,
                self._format_size(file_size),
                chat_count,
                screenshot_count,
            )

    async def run(self, stop_event: asyncio.Event):
        while not stop_event.is_set():
            try:
                lives, ok = await self.detector.poll()
                if ok:
                    await self.sync(lives)
                    await self.check_health()
                    self.log_progress()
            except Exception as e:
                self.log.error("Loop error: %s", e)

            try:
                await asyncio.wait_for(
                    stop_event.wait(), timeout=self.config.poll_interval
                )
                break
            except asyncio.TimeoutError:
                pass
        self.log.info("Shutting down...")
        await self.shutdown()
        self.log.info("Goodbye.")

    @staticmethod
    def _format_duration(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}h{m:02d}m"
        return f"{m:02d}m{s:02d}s"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.0f}KB"
        return f"{size_bytes / (1024 * 1024):.1f}MB"

    async def _start_session(self, live: LiveInfo):
        recordings_dir = self.config.recordings_dir

        resumed_folder = None
        resumed_mkv_parts = []
        resumed_start_time = time.time()

        json_files = glob.glob(
            os.path.join(recordings_dir, "*", f"{live.live_id}.json")
        )
        for jf in json_files:
            try:
                with open(jf, "r") as f:
                    data = json.load(f)
                if data.get("live_id") == live.live_id and data.get("status") in (
                    "interrupted",
                    "recording",
                    "completed",
                ):
                    resumed_folder = os.path.dirname(jf)
                    resumed_mkv_parts = data.get("mkv_parts", [])
                    rec_started = data.get("recording_started_at")
                    if rec_started:
                        try:
                            dt = datetime.strptime(rec_started, "%Y-%m-%dT%H:%M:%SZ")
                            dt = dt.replace(tzinfo=timezone.utc)
                            resumed_start_time = dt.timestamp()
                        except Exception:
                            pass
                    break
            except Exception:
                pass

        if resumed_folder:
            live_folder = resumed_folder
            recording_start_time = resumed_start_time

            valid_mkv_parts = []
            for p in resumed_mkv_parts:
                if os.path.exists(p):
                    valid_mkv_parts.append(p)
            resumed_mkv_parts = valid_mkv_parts

            mp4_path = os.path.join(live_folder, f"{live.live_id}.mp4")
            if os.path.exists(mp4_path):
                part_idx = len(resumed_mkv_parts) + 1
                new_part_path = os.path.join(
                    live_folder, f"{live.live_id}_part{part_idx}.mp4"
                )
                try:
                    os.rename(mp4_path, new_part_path)
                    resumed_mkv_parts.append(new_part_path)
                except Exception as e:
                    self.log.warning("Failed to rename existing mp4 for resume: %s", e)

            r2_done_path = os.path.join(live_folder, ".r2_done")
            if os.path.exists(r2_done_path):
                try:
                    os.remove(r2_done_path)
                except Exception:
                    pass

            uri_path = os.path.join(live_folder, f"{live.live_id}.upload_uri")
            if os.path.exists(uri_path):
                try:
                    os.remove(uri_path)
                except Exception:
                    pass

            abort_path = os.path.join(live_folder, ".abort_upload")
            try:
                open(abort_path, "w").close()
            except Exception:
                pass

            mkv_parts = resumed_mkv_parts
            self.log.info(
                "Resuming interrupted session for %s in %s", live.live_id, live_folder
            )
        else:
            start_at_unix = _parse_start_at(live.start_at)
            nickname_lower = _sanitize_filename(live.member_nickname)
            live_folder = os.path.join(
                recordings_dir, f"{nickname_lower}_{start_at_unix}"
            )
            os.makedirs(live_folder, exist_ok=True)
            recording_start_time = time.time()
            mkv_parts = []

        screenshots_folder = os.path.join(live_folder, "screenshots")
        if live.record:
            os.makedirs(screenshots_folder, exist_ok=True)

        base = live.live_id
        mkv_path = os.path.join(live_folder, f"{base}.mkv")

        if resumed_folder and os.path.exists(mkv_path):
            if os.path.getsize(mkv_path) > 1024:
                part_idx = len(mkv_parts) + 1
                new_mkv = mkv_path.replace(".mkv", f"_part{part_idx}.mkv")
                try:
                    os.rename(mkv_path, new_mkv)
                    mkv_parts.append(new_mkv)
                except Exception:
                    pass
            else:
                try:
                    os.remove(mkv_path)
                except Exception:
                    pass

        chat_log_path = os.path.join(live_folder, f"{base}.log")
        jsonl_path = os.path.join(live_folder, f"{base}.jsonl")
        srt_path = os.path.join(live_folder, f"{base}.srt")
        json_path = os.path.join(live_folder, f"{base}.json")
        thumbnail_path = os.path.join(live_folder, f"{base}.jpg")

        open(chat_log_path, "a").close()
        open(jsonl_path, "a").close()

        stream_info, _ = await self.detector.get_streaming_url(
            live.platform, live.room_id, live.live_id
        )
        if not stream_info:
            self.log.warning("Failed to get streaming URL for %s", live.live_id)
            return

        hls_url = self.detector.pick_best_url(stream_info)
        if not hls_url:
            hls_url = live.hls_url

        if not hls_url:
            self.log.warning("No streaming URLs for %s", live.live_id)
            return

        if stream_info.get("room_identifier"):
            live.room_identifier = stream_info.get("room_identifier")

        ffmpeg_proc = None
        if not live.record:
            self.log.info(
                "Recording disabled for %s (record=False). Chat+gift will still be captured.",
                live.live_id,
            )
        if live.record:
            ffmpeg_proc = stream_recorder.start(
                hls_url, mkv_path, headers=self._get_platform_headers(live)
            )

        stop_event = asyncio.Event()
        self._stop_events[live.live_id] = stop_event

        chat_task = None
        gift_task = None

        if live.platform == "showroom":
            chat_task = asyncio.create_task(
                chat_capture.capture_showroom(
                    self.config.api_base_url,
                    live.room_id,
                    chat_log_path,
                    jsonl_path,
                    recording_start_time,
                    self.config.showroom_comment_interval,
                    stop_event,
                )
            )
            gift_task = asyncio.create_task(
                chat_capture.capture_showroom_gifts(
                    self.config.api_base_url,
                    live.room_id,
                    chat_log_path,
                    jsonl_path,
                    recording_start_time,
                    self.config.showroom_gift_interval,
                    stop_event,
                )
            )
        elif live.platform == "idn" and live.room_identifier:
            chat_task = asyncio.create_task(
                chat_capture.capture_idn(
                    live.room_identifier,
                    chat_log_path,
                    jsonl_path,
                    recording_start_time,
                    stop_event,
                )
            )
        elif live.platform == "idn" and not live.room_identifier:
            self.log.warning(
                "No room_identifier for IDN live %s, will retry", live.live_id
            )
            chat_task = asyncio.create_task(
                self._retry_idn_room(
                    live.live_id,
                    live.room_id,
                    live.live_id,
                    chat_log_path,
                    jsonl_path,
                    recording_start_time,
                    stop_event,
                )
            )
        else:
            chat_task = None
            gift_task = None

        session = RecordingSession(
            live_id=live.live_id,
            platform=live.platform,
            member_name=live.member_name,
            member_nickname=live.member_nickname,
            room_id=live.room_id,
            room_identifier=live.room_identifier,
            room_url_key=live.room_url_key,
            hls_url=hls_url,
            recording_start_time=recording_start_time,
            output_path=mkv_path,
            chat_log_path=chat_log_path,
            srt_path=srt_path,
            json_path=json_path,
            jsonl_path=jsonl_path,
            thumbnail_path=thumbnail_path,
            screenshots_folder=screenshots_folder,
            live_folder=live_folder,
            title=live.title,
            gift_task=gift_task,
            member_image=live.member_image,
            start_at=live.start_at,
            live_type=live.live_type,
            ffmpeg_proc=ffmpeg_proc,
            chat_task=chat_task,
            mkv_parts=mkv_parts,
        )

        self.sessions[live.live_id] = session

        # Write initial JSON with status "recording" as safety net for crash recovery
        try:
            initial_metadata = {
                "live_id": session.live_id,
                "status": "recording",
                "platform": session.platform,
                "room_id": session.room_id if session.platform == "showroom" else None,
                "room_identifier": session.room_identifier,
                "title": session.title,
                "member_name": session.member_name,
                "member_nickname": session.member_nickname,
                "start_at": session.start_at,
                "live_type": session.live_type,
                "recording_started_at": datetime.fromtimestamp(
                    session.recording_start_time, tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "mkv_parts": session.mkv_parts,
            }
            with open(session.json_path, "w") as f:
                json.dump(initial_metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log.warning("Failed to write initial JSON: %s", e)

        if live.record:
            asyncio.create_task(self._periodic_thumbnails(session))
            asyncio.create_task(self._capture_initial_thumbnail(session))

        if not resumed_folder:
            asyncio.create_task(
                telegram_notifier.send_live_start_notification(live, self.config)
            )

        self.log.info(
            "%s %s/%s (%s)",
            "Started recording" if live.record else "Monitoring chat+gift for",
            live.platform,
            live.member_name,
            live.live_id,
        )

    async def _retry_idn_room(
        self,
        live_id: str,
        room_id: str,
        id_live_id: str,
        chat_log_path: str,
        jsonl_path: str,
        recording_start_time: float,
        stop_event: asyncio.Event,
    ):
        for attempt in range(1, 11):
            await asyncio.sleep(15)
            if stop_event.is_set():
                return
            session = self.sessions.get(live_id)
            if not session or (
                session.room_identifier
                and str(session.room_identifier).startswith("arn:")
            ):
                return
            info, _ = await self.detector.get_streaming_url("idn", room_id, id_live_id)
            if info and info.get("room_identifier"):
                rid = info.get("room_identifier")
                session.room_identifier = rid
                self.log.info(
                    "Got room_identifier for %s, starting chat capture", live_id
                )
                try:
                    await chat_capture.capture_idn(
                        rid, chat_log_path, jsonl_path, recording_start_time, stop_event
                    )
                except asyncio.CancelledError:
                    pass
                return
            self.log.warning(
                "Retry room_identifier %d/10 for %s — still null", attempt, live_id
            )
        self.log.error("Failed to get room_identifier for %s after 10 retries", live_id)

    async def _capture_screenshot(
        self,
        source: str,
        dest: str,
        seek: str,
        timeout: int = 30,
        *,
        live: bool = False,
        headers: dict = None,
    ):
        header_args = []
        if headers:
            header_str = "".join([f"{k}: {v}\r\n" for k, v in headers.items()])
            header_args.extend(["-headers", header_str])

        if live:
            for attempt in range(1, 4):
                try:
                    args = (
                        [
                            "ffmpeg",
                            "-loglevel",
                            "error",
                        ]
                        + header_args
                        + [
                            "-i",
                            source,
                            "-vframes",
                            "1",
                            "-strict",
                            "unofficial",
                            "-y",
                            dest,
                        ]
                    )
                    r = await asyncio.create_subprocess_exec(
                        *args,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    _, stderr = await asyncio.wait_for(r.communicate(), timeout=120)
                    if (
                        r.returncode == 0
                        and os.path.exists(dest)
                        and os.path.getsize(dest) > 0
                    ):
                        self.log.info("  screenshot (HLS) OK")
                        return True
                    err_msg = stderr.decode(errors="ignore").strip()[:200]
                    self.log.info(
                        "  screenshot (HLS attempt %d/3): %s",
                        attempt,
                        err_msg or "failed",
                    )
                except asyncio.TimeoutError:
                    self.log.info("  screenshot (HLS attempt %d/3): timeout", attempt)
                except Exception as e:
                    self.log.info("  screenshot (HLS attempt %d/3): %s", attempt, e)
                await asyncio.sleep(5)
            return False

        strategies = [
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-ss",
                seek,
                *header_args,
                "-i",
                source,
                "-vframes",
                "1",
                "-strict",
                "unofficial",
                "-y",
                dest,
            ],
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-fflags",
                "+genpts",
                "-analyzeduration",
                "1000000",
                "-ss",
                seek,
                *header_args,
                "-i",
                source,
                "-vframes",
                "1",
                "-strict",
                "unofficial",
                "-y",
                dest,
            ],
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-skip_frame",
                "nokey",
                *header_args,
                "-i",
                source,
                "-ss",
                seek,
                "-vframes",
                "1",
                "-strict",
                "unofficial",
                "-y",
                dest,
            ],
            [
                "ffmpeg",
                "-loglevel",
                "error",
                *header_args,
                "-i",
                source,
                "-ss",
                seek,
                "-vframes",
                "1",
                "-strict",
                "unofficial",
                "-y",
                dest,
            ],
        ]

        last_err = ""
        for i, cmd in enumerate(strategies):
            strategy_name = ["fast seek", "+genpts", "skip_frame nokey", "full scan"][i]
            try:
                r = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    _, stderr = await asyncio.wait_for(r.communicate(), timeout=timeout)
                except asyncio.TimeoutError:
                    r.kill()
                    await r.wait()
                    self.log.info("  strategy %d/4 (%s): timeout", i + 1, strategy_name)
                    continue

                if r.returncode != 0:
                    last_err = stderr.decode(errors="ignore").strip()
                    self.log.info(
                        "  strategy %d/4 (%s): failed (%s)",
                        i + 1,
                        strategy_name,
                        last_err[:80],
                    )
                    continue

                if not os.path.exists(dest) or os.path.getsize(dest) == 0:
                    last_err = stderr.decode(errors="ignore").strip()
                    self.log.info(
                        "  strategy %d/4 (%s): empty output", i + 1, strategy_name
                    )
                    continue

                self.log.info(
                    "  screenshot OK with strategy %d/4 (%s)", i + 1, strategy_name
                )
                return True
            except Exception as e:
                last_err = str(e)
                self.log.info(
                    "  strategy %d/4 (%s): exception (%s)", i + 1, strategy_name, e
                )
                continue

        self.log.warning("Screenshot file missing/empty: %s", dest)
        if last_err:
            self.log.warning("  ffmpeg stderr: %s", last_err)
        return False

    def _get_platform_headers(self, obj: LiveInfo | RecordingSession) -> dict | None:
        if obj.platform == "idn":
            return {
                "Origin": "https://www.idn.app",
                "Referer": "https://www.idn.app/",
            }
        return None

    async def _get_fresh_hls_url(self, session: RecordingSession) -> str:
        if session.platform == "idn" and session.live_type != "public":
            stream_info, _ = await self.detector.get_streaming_url(
                session.platform, session.room_id, session.live_id
            )
            if stream_info:
                fresh_url = self.detector.pick_best_url(stream_info)
                if fresh_url:
                    return fresh_url
        return session.hls_url

    async def _capture_initial_thumbnail(self, session: RecordingSession):
        await asyncio.sleep(30)
        if session.live_id not in self.sessions:
            return
        self.log.info("Initial thumb: capturing at 30s...")
        ts = int(time.time())
        ss_name = f"{_sanitize_filename(session.member_nickname)}_{ts}.jpg"
        ss_path = os.path.join(session.screenshots_folder, ss_name)

        headers = self._get_platform_headers(session)
        ss_url = await self._get_fresh_hls_url(session)
        self.log.info("Initial thumb URL: %s | headers: %s", ss_url, headers)

        ok = await self._capture_screenshot(
            ss_url, ss_path, "5", 30, live=True, headers=headers
        )
        if ok:
            self.log.info("Initial screenshot saved: %s", ss_name)
        else:
            self.log.warning("Initial screenshot FAILED")

    async def _periodic_thumbnails(self, session: RecordingSession):
        await asyncio.sleep(300)
        self.log.info("Periodic thumb: starting 5-min cycle")

        headers = self._get_platform_headers(session)

        while session.live_id in self.sessions:
            elapsed = int(time.time() - session.recording_start_time)
            seek = str(max(5, elapsed - 30))
            ts = int(time.time())
            ss_name = f"{_sanitize_filename(session.member_nickname)}_{ts}.jpg"
            ss_path = os.path.join(session.screenshots_folder, ss_name)

            ss_url = await self._get_fresh_hls_url(session)
            self.log.info("Periodic thumb URL: %s | headers: %s", ss_url, headers)
            ok = await self._capture_screenshot(
                ss_url, ss_path, seek, 30, live=True, headers=headers
            )
            if ok:
                self.log.info("Screenshot at %ss: %s", seek, ss_name)
            else:
                self.log.warning("Periodic screenshot FAILED at %ss", seek)
            await asyncio.sleep(300)

    async def _end_session(self, live_id: str, reason: str = "completed"):
        if live_id in self._pending_ends:
            return

        session = self.sessions.get(live_id)
        if not session:
            return

        self._pending_ends.add(live_id)

        if reason == "completed":
            abort_path = os.path.join(session.live_folder, ".abort_upload")
            if os.path.exists(abort_path):
                try:
                    os.remove(abort_path)
                except Exception:
                    pass

        self.log.info(
            "Ending recording %s/%s (%s)",
            session.platform,
            session.member_name,
            live_id,
        )

        recording_ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if live_id in self._stop_events:
            self._stop_events[live_id].set()

        if session.chat_task:
            session.chat_task.cancel()
            try:
                await session.chat_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                self.log.error("Chat task error for %s: %s", live_id, e)

        if session.gift_task:
            session.gift_task.cancel()
            try:
                await session.gift_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                self.log.error("Gift task error for %s: %s", live_id, e)

        if session.ffmpeg_proc:
            stream_recorder.stop(session.ffmpeg_proc)

        mkv_path = session.output_path
        mp4_path = os.path.splitext(mkv_path)[0] + ".mp4"
        remux_ok = False

        if reason == "interrupted":
            if os.path.exists(mkv_path):
                if os.path.getsize(mkv_path) > 1024:
                    part_idx = len(session.mkv_parts) + 1
                    new_mkv = mkv_path.replace(".mkv", f"_part{part_idx}.mkv")
                    try:
                        os.rename(mkv_path, new_mkv)
                        session.mkv_parts.append(new_mkv)
                    except Exception:
                        pass
                else:
                    try:
                        os.remove(mkv_path)
                    except Exception:
                        pass

        parts_to_concat = session.mkv_parts.copy() if reason != "interrupted" else []
        if os.path.exists(mkv_path) and reason != "interrupted":
            parts_to_concat.append(mkv_path)

        if parts_to_concat:
            if len(parts_to_concat) == 1:
                target_mkv = parts_to_concat[0]
                try:
                    await asyncio.to_thread(
                        subprocess.run,
                        [
                            "ffmpeg",
                            "-fflags",
                            "+genpts",
                            "-i",
                            target_mkv,
                            "-c",
                            "copy",
                            "-avoid_negative_ts",
                            "make_zero",
                            "-bsf:a",
                            "aac_adtstoasc",
                            "-movflags",
                            "+faststart",
                            "-y",
                            mp4_path,
                        ],
                        capture_output=True,
                        timeout=self.config.remux_timeout,
                    )
                    os.remove(target_mkv)
                    session.output_path = mp4_path
                    remux_ok = True
                    self.log.info("Remuxed to MP4: %s", mp4_path)
                except Exception as e:
                    self.log.warning("Remux failed: %s", e)
            else:
                concat_list_path = os.path.join(session.live_folder, "concat.txt")
                normalized_parts = []
                try:
                    # Normalize all parts to MKV first to avoid timestamp issues
                    for p in parts_to_concat:
                        if p.endswith(".mp4"):
                            norm_mkv = p.replace(".mp4", "_norm.mkv")
                            await asyncio.to_thread(
                                subprocess.run,
                                [
                                    "ffmpeg",
                                    "-fflags",
                                    "+genpts+igndts",
                                    "-i",
                                    p,
                                    "-c",
                                    "copy",
                                    "-y",
                                    norm_mkv,
                                ],
                                capture_output=True,
                                timeout=self.config.remux_timeout,
                            )
                            normalized_parts.append(norm_mkv)
                        else:
                            normalized_parts.append(p)

                    with open(concat_list_path, "w") as f:
                        for p in normalized_parts:
                            f.write(f"file '{os.path.abspath(p)}'\n")

                    temp_mkv = os.path.join(
                        session.live_folder,
                        f"{session.live_id}_concat.mkv",
                    )
                    await asyncio.to_thread(
                        subprocess.run,
                        [
                            "ffmpeg",
                            "-fflags",
                            "+genpts+igndts",
                            "-f",
                            "concat",
                            "-safe",
                            "0",
                            "-i",
                            concat_list_path,
                            "-c",
                            "copy",
                            "-avoid_negative_ts",
                            "make_zero",
                            "-y",
                            temp_mkv,
                        ],
                        capture_output=True,
                        timeout=self.config.remux_timeout,
                    )

                    # Remux the concatenated MKV to final MP4
                    await asyncio.to_thread(
                        subprocess.run,
                        [
                            "ffmpeg",
                            "-fflags",
                            "+genpts",
                            "-i",
                            temp_mkv,
                            "-c",
                            "copy",
                            "-bsf:a",
                            "aac_adtstoasc",
                            "-movflags",
                            "+faststart",
                            "-y",
                            mp4_path,
                        ],
                        capture_output=True,
                        timeout=self.config.remux_timeout,
                    )

                    # Cleanup all intermediate files
                    for p in parts_to_concat:
                        try:
                            os.remove(p)
                        except Exception:
                            pass
                    for p in normalized_parts:
                        if p not in parts_to_concat:
                            try:
                                os.remove(p)
                            except Exception:
                                pass
                    try:
                        os.remove(temp_mkv)
                    except Exception:
                        pass
                    try:
                        os.remove(concat_list_path)
                    except Exception:
                        pass

                    session.output_path = mp4_path
                    remux_ok = True
                    self.log.info(
                        "Remuxed to MP4 (concat %d parts): %s",
                        len(parts_to_concat),
                        mp4_path,
                    )
                except Exception as e:
                    self.log.warning("Concat remux failed: %s", e)

        final_mp4 = mp4_path if os.path.exists(mp4_path) else mkv_path
        duration = 0
        if os.path.exists(final_mp4) and reason != "interrupted":
            duration = _get_duration(final_mp4)
            if duration <= 0:
                duration = time.time() - session.recording_start_time
            if duration > 0:
                target_sec = min(int(duration * 0.5), 300)
            else:
                target_sec = 0
            try:
                ts = int(time.time())
                ss_path = os.path.join(
                    session.screenshots_folder,
                    f"{_sanitize_filename(session.member_nickname)}_{ts}.jpg",
                )
                r = await asyncio.to_thread(
                    subprocess.run,
                    [
                        "ffmpeg",
                        "-loglevel",
                        "error",
                        "-ss",
                        str(target_sec),
                        "-i",
                        final_mp4,
                        "-vframes",
                        "1",
                        "-strict",
                        "unofficial",
                        "-y",
                        ss_path,
                    ],
                    capture_output=True,
                    timeout=30,
                )
                if r.returncode == 0 and os.path.exists(ss_path):
                    self.log.info(
                        "Final screenshot captured: %s", os.path.basename(ss_path)
                    )
                elif r.returncode != 0:
                    self.log.warning(
                        "Final screenshot failed: %s",
                        r.stderr.decode(errors="ignore").strip(),
                    )
            except Exception as e:
                self.log.error("Screenshot error: %s", e)

        if os.path.exists(session.chat_log_path) and reason != "interrupted":
            try:
                srt_generator.generate(session.chat_log_path, session.srt_path)
                self.log.info("SRT generated: %s", session.srt_path)
            except Exception as e:
                self.log.warning("SRT generation failed: %s", e)

        try:
            metadata = {
                "live_id": session.live_id,
                "status": reason,
                "platform": session.platform,
                "room_id": session.room_id if session.platform == "showroom" else None,
                "room_identifier": session.room_identifier,
                "title": session.title,
                "member_name": session.member_name,
                "member_nickname": session.member_nickname,
                "start_at": session.start_at,
                "recording_started_at": datetime.fromtimestamp(
                    session.recording_start_time, tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "recording_ended_at": recording_ended_at,
                "duration_seconds": int(duration)
                if duration > 0
                else int(time.time() - session.recording_start_time),
                "srt_file": os.path.basename(session.srt_path),
                "youtube_id": None,
                "youtube_title": None,
                "live_type": session.live_type,
                "mkv_parts": session.mkv_parts,
            }
            with open(session.json_path, "w") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            self.log.info("JSON metadata: %s", session.json_path)

            if reason == "completed":
                metadata["end_at"] = recording_ended_at
                asyncio.create_task(
                    telegram_notifier.send_end_live_notification(self.config, metadata)
                )

        except Exception as e:
            self.log.error("JSON write failed: %s", e)

        if remux_ok:
            for fpath in [session.chat_log_path]:
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass

            ffmpeg_log = (
                os.path.splitext(session.output_path)[0].replace(".mp4", "")
                + ".ffmpeg.log"
            )
            if os.path.exists(ffmpeg_log):
                try:
                    os.remove(ffmpeg_log)
                except Exception:
                    pass

        self.sessions.pop(live_id, None)
        self._stop_events.pop(live_id, None)
        self._pending_ends.discard(live_id)

        self.log.info(
            "Finished recording %s/%s with status %s",
            session.platform,
            session.member_name,
            reason.upper(),
        )

    async def shutdown(self):
        for live_id in list(self.sessions.keys()):
            await self._end_session(live_id, reason="interrupted")
        await self.detector.close()

    def check_status_cli(self, folder: str):
        recordings_dir = self.config.recordings_dir
        if folder == "all":
            json_files = glob.glob(os.path.join(recordings_dir, "*", "*.json"))
        else:
            json_files = glob.glob(os.path.join(recordings_dir, folder, "*.json"))

        self.log.info("--- Recordings Status ---")
        found = 0
        for jf in json_files:
            try:
                with open(jf, "r") as f:
                    data = json.load(f)
                status = data.get("status", "unknown")
                live_id = data.get("live_id", "unknown")
                mkv_parts = data.get("mkv_parts", [])
                parent_folder = os.path.basename(os.path.dirname(jf))
                self.log.info(
                    f"[{status.upper()}] Folder: {parent_folder} | Live: {live_id} | Parts: {len(mkv_parts)}"
                )
                found += 1
            except Exception:
                pass

        if found == 0:
            self.log.info("No recordings found matching criteria.")

    async def force_remux(self, folder: str):
        recordings_dir = self.config.recordings_dir
        if folder == "all":
            json_files = glob.glob(os.path.join(recordings_dir, "*", "*.json"))
        else:
            json_files = glob.glob(os.path.join(recordings_dir, folder, "*.json"))

        processed = 0
        for jf in json_files:
            try:
                with open(jf, "r") as f:
                    data = json.load(f)
            except Exception as e:
                self.log.error(f"Failed to read {jf}: {e}")
                continue

            status = data.get("status", "")
            if status == "completed":
                self.log.info(f"Skipping {jf} (Status is already completed)")
                continue

            live_id = data.get("live_id")
            if not live_id:
                continue

            processed += 1
            live_folder = os.path.dirname(jf)
            self.log.info(f"Force remuxing interrupted session: {live_folder}")

            rec_started = data.get("recording_started_at")
            resumed_start_time = time.time()
            if rec_started:
                try:
                    dt = datetime.strptime(rec_started, "%Y-%m-%dT%H:%M:%SZ")
                    dt = dt.replace(tzinfo=timezone.utc)
                    resumed_start_time = dt.timestamp()
                except Exception:
                    pass

            session = RecordingSession(
                live_id=live_id,
                platform=data.get("platform", "unknown"),
                member_name=data.get("member_name", "unknown"),
                member_nickname=data.get("member_nickname", "unknown"),
                room_id=data.get("room_id", ""),
                room_identifier=data.get("room_identifier", ""),
                room_url_key=data.get("room_url_key", ""),
                hls_url="",
                recording_start_time=resumed_start_time,
                output_path=os.path.join(live_folder, f"{live_id}.mkv"),
                chat_log_path=os.path.join(live_folder, f"{live_id}.log"),
                srt_path=os.path.join(live_folder, f"{live_id}.srt"),
                json_path=jf,
                jsonl_path=os.path.join(live_folder, f"{live_id}.jsonl"),
                thumbnail_path=os.path.join(live_folder, f"{live_id}.jpg"),
                screenshots_folder=os.path.join(live_folder, "screenshots"),
                live_folder=live_folder,
                title=data.get("title", ""),
                member_image="",
                start_at=data.get("start_at", ""),
                mkv_parts=data.get("mkv_parts", []),
            )

            self.sessions[live_id] = session
            await self._end_session(live_id, reason="completed")

        if processed == 0:
            self.log.info("No recordings found matching criteria to remux.")

    def delete_recordings_cli(self, folder: str, force: bool = False):
        recordings_dir = self.config.recordings_dir
        if folder == "all":
            folders = glob.glob(os.path.join(recordings_dir, "*"))
        else:
            folders = glob.glob(os.path.join(recordings_dir, folder))

        folders_to_delete = [f for f in folders if os.path.isdir(f)]

        if not folders_to_delete:
            self.log.info("No recording folders found to delete.")
            return

        if folder == "all":
            warning_msg = f"WARNING: You are about to delete ALL {len(folders_to_delete)} recording folders in {recordings_dir}."
            folder_list = "\n".join(
                f"  - {os.path.basename(f)}" for f in folders_to_delete
            )
            warning_msg = f"{warning_msg}\n{folder_list}"
        else:
            warning_msg = f"WARNING: You are about to delete the folder: {os.path.basename(folders_to_delete[0])}."

        if not force:
            sys.stderr.write(f"\n{warning_msg}\n")
            sys.stderr.write("Are you sure you want to continue? (y/N): ")
            sys.stderr.flush()

            try:
                import termios

                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                new_settings = termios.tcgetattr(fd)
                # Force canonical mode + echo + translate CR to NL
                new_settings[0] = new_settings[0] | termios.ICRNL
                new_settings[3] = new_settings[3] | termios.ICANON | termios.ECHO
                termios.tcsetattr(fd, termios.TCSANOW, new_settings)
                answer = sys.stdin.readline().strip()
                termios.tcsetattr(fd, termios.TCSANOW, old_settings)
            except (ImportError, termios.error):
                answer = sys.stdin.readline().strip()

            if answer.lower() not in ["y", "yes"]:
                self.log.info("Deletion aborted by user.")
                return

        deleted = 0
        for f in folders_to_delete:
            try:
                shutil.rmtree(f)
                self.log.info(f"Deleted folder: {os.path.basename(f)}")
                deleted += 1
            except Exception as e:
                self.log.error(f"Failed to delete {f}: {e}")

        self.log.info(f"Successfully deleted {deleted} folders.")
