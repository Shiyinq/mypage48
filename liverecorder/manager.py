import asyncio
import json
import os
import subprocess
import time
from datetime import datetime, timezone

from .config import RecorderConfig
from .live_detector import LiveDetector
from .models import LiveInfo, RecordingSession

from . import stream_recorder
from . import chat_capture
from . import srt_generator


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
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of",
             "default=noprint_wrappers=1:nokey=1", mp4_path],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    return 0.0


class RecordingManager:
    def __init__(self, config: RecorderConfig):
        self.config = config
        self.detector = LiveDetector(config.api_base_url)
        self.sessions: dict[str, RecordingSession] = {}
        self._stop_events: dict[str, asyncio.Event] = {}

    async def sync(self, current_lives: list[LiveInfo]):
        current_ids = {l.live_id for l in current_lives}

        for live in current_lives:
            if live.live_id not in self.sessions:
                await self._start_session(live)

        ended_ids = set(self.sessions.keys()) - current_ids
        for live_id in ended_ids:
            await self._end_session(live_id, reason="completed")

    async def check_health(self):
        dead_ids = []
        now = time.time()
        for live_id, session in self.sessions.items():
            if session.ffmpeg_proc and not stream_recorder.is_running(session.ffmpeg_proc):
                print(f"[manager] ffmpeg died for {live_id}")
                dead_ids.append(live_id)
                continue
            if os.path.exists(session.output_path):
                age = now - os.path.getmtime(session.output_path)
                if age > 120:
                    print(f"[manager] ffmpeg stalled for {live_id} (file age: {age:.0f}s)")
                    dead_ids.append(live_id)

        for live_id in dead_ids:
            await self._end_session(live_id, reason="error")

    def log_progress(self):
        if not self.sessions:
            return

        print("Recording Progress:")
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

            print(f"  {session.member_nickname} ({session.platform}) | {duration_str} | {self._format_size(file_size)} | {chat_count} chats")

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

        start_at_unix = _parse_start_at(live.start_at)
        nickname_lower = live.member_nickname.lower().replace(" ", "_").replace("/", "_")
        live_folder = os.path.join(recordings_dir, f"{nickname_lower}_{start_at_unix}")
        os.makedirs(live_folder, exist_ok=True)

        screenshots_folder = os.path.join(live_folder, "screenshots")
        os.makedirs(screenshots_folder, exist_ok=True)

        base = live.live_id
        mkv_path = os.path.join(live_folder, f"{base}.mkv")
        chat_log_path = os.path.join(live_folder, f"{base}.log")
        jsonl_path = os.path.join(live_folder, f"{base}.jsonl")
        srt_path = os.path.join(live_folder, f"{base}.srt")
        json_path = os.path.join(live_folder, f"{base}.json")
        thumbnail_path = os.path.join(live_folder, f"{base}.jpg")

        open(chat_log_path, "w").close()
        open(jsonl_path, "w").close()

        hls_url = live.hls_url
        stream_info = await self.detector.get_streaming_url(
            live.platform, live.room_id, live.live_id
        )
        if not stream_info:
            print(f"[manager] Failed to get streaming URL for {live.live_id}")
            return

        if not hls_url:
            hls_url = self.detector.pick_best_url(stream_info)
            if not hls_url:
                print(f"[manager] No streaming URLs for {live.live_id}")
                return

        if not live.room_identifier:
            live.room_identifier = stream_info.get("room_identifier")

        recording_start_time = time.time()

        ffmpeg_proc = stream_recorder.start(hls_url, mkv_path)

        stop_event = asyncio.Event()
        self._stop_events[live.live_id] = stop_event

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
            print(f"[manager] No room_identifier for IDN live {live.live_id}, will retry")
            chat_task = asyncio.create_task(
                self._retry_idn_room(
                    live.live_id, live.room_id, live.live_id,
                    chat_log_path, jsonl_path, recording_start_time, stop_event,
                )
            )
        else:
            chat_task = None

        session = RecordingSession(
            live_id=live.live_id,
            platform=live.platform,
            member_name=live.member_name,
            member_nickname=live.member_nickname,
            room_id=live.room_id,
            room_identifier=live.room_identifier,
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
            member_image=live.member_image,
            start_at=live.start_at,
            ffmpeg_proc=ffmpeg_proc,
            chat_task=chat_task,
        )

        self.sessions[live.live_id] = session

        asyncio.create_task(self._periodic_thumbnails(session))
        asyncio.create_task(self._capture_initial_thumbnail(session))

        print(f"[manager] Started recording {live.platform}/{live.member_name} ({live.live_id})")

    async def _retry_idn_room(
        self, live_id: str, room_id: str, id_live_id: str,
        chat_log_path: str, jsonl_path: str,
        recording_start_time: float, stop_event: asyncio.Event,
    ):
        for attempt in range(1, 11):
            await asyncio.sleep(15)
            if stop_event.is_set():
                return
            session = self.sessions.get(live_id)
            if not session or session.room_identifier:
                return
            info = await self.detector.get_streaming_url("idn", room_id, id_live_id)
            if info and info.get("room_identifier"):
                rid = info.get("room_identifier")
                session.room_identifier = rid
                print(f"[manager] Got room_identifier for {live_id}, starting chat capture")
                try:
                    await chat_capture.capture_idn(rid, chat_log_path, jsonl_path, recording_start_time, stop_event)
                except asyncio.CancelledError:
                    pass
                return
            print(f"[manager] Retry room_identifier {attempt}/10 for {live_id} — still null")
        print(f"[manager] Failed to get room_identifier for {live_id} after 10 retries")

    async def _capture_screenshot(self, source: str, dest: str, seek: str, timeout: int = 30):
        try:
            r = await asyncio.create_subprocess_exec(
                "ffmpeg", "-loglevel", "error",
                "-ss", seek, "-i", source,
                "-vframes", "1",
                "-strict", "unofficial",
                "-y", dest,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                _, stderr = await asyncio.wait_for(r.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                r.kill()
                await r.wait()
                return False
            if r.returncode != 0:
                err = stderr.decode(errors='ignore').strip()
                print(f"[manager] ffmpeg screenshot failed (seek={seek}): {err}")
                return False
            if not os.path.exists(dest) or os.path.getsize(dest) == 0:
                err = stderr.decode(errors='ignore').strip()
                print(f"[manager] Screenshot file missing/empty: {dest}")
                if err:
                    print(f"[manager]   ffmpeg stderr: {err}")
                return False
            return True
        except Exception as e:
            print(f"[manager] screenshot error: {e}")
            return False

    async def _capture_initial_thumbnail(self, session: RecordingSession):
        await asyncio.sleep(30)
        if session.live_id not in self.sessions:
            return
        if not os.path.exists(session.output_path):
            print(f"[manager] Initial thumb: {session.output_path} not found, skipping")
            return
        print(f"[manager] Initial thumb: capturing at 30s...")
        ts = int(time.time())
        ss_name = f"{session.member_nickname.lower()}_{ts}.jpg"
        ss_path = os.path.join(session.screenshots_folder, ss_name)
        ok = await self._capture_screenshot(session.output_path, ss_path, "5", 30)
        if ok:
            print(f"[manager] Initial screenshot saved: {ss_name}")
        else:
            print(f"[manager] Initial screenshot FAILED")

    async def _periodic_thumbnails(self, session: RecordingSession):
        await asyncio.sleep(300)
        print(f"[manager] Periodic thumb: starting 5-min cycle")
        while session.live_id in self.sessions:
            if not os.path.exists(session.output_path):
                print(f"[manager] Periodic thumb: {session.output_path} gone, stopping")
                break
            elapsed = int(time.time() - session.recording_start_time)
            seek = str(max(5, elapsed - 30))
            ts = int(time.time())
            ss_name = f"{session.member_nickname.lower()}_{ts}.jpg"
            ss_path = os.path.join(session.screenshots_folder, ss_name)
            ok = await self._capture_screenshot(session.output_path, ss_path, seek, 30)
            if ok:
                print(f"[manager] Screenshot at {seek}s: {ss_name}")
            else:
                print(f"[manager] Periodic screenshot FAILED at {seek}s")
            await asyncio.sleep(300)

    async def _end_session(self, live_id: str, reason: str = "completed"):
        session = self.sessions.get(live_id)
        if not session:
            return

        print(f"[manager] Ending recording {session.platform}/{session.member_name} ({live_id})")

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
                print(f"[manager] Chat task error for {live_id}: {e}")

        if session.ffmpeg_proc:
            stream_recorder.stop(session.ffmpeg_proc)

        mkv_path = session.output_path
        mp4_path = os.path.splitext(mkv_path)[0] + ".mp4"
        remux_ok = False

        if os.path.exists(mkv_path):
            try:
                subprocess.run(
                    ["ffmpeg", "-i", mkv_path, "-c", "copy",
                     "-bsf:a", "aac_adtstoasc", "-movflags", "+faststart",
                     "-y", mp4_path],
                    capture_output=True, timeout=300,
                )
                os.remove(mkv_path)
                session.output_path = mp4_path
                remux_ok = True
                print(f"[manager] Remuxed to MP4: {mp4_path}")
            except Exception as e:
                print(f"[manager] Remux failed: {e}")

        final_mp4 = mp4_path if os.path.exists(mp4_path) else mkv_path
        duration = 0
        if os.path.exists(final_mp4):
            duration = _get_duration(final_mp4)
            if duration <= 0:
                duration = time.time() - session.recording_start_time
            if duration > 0:
                target_sec = min(int(duration * 0.5), 300)
            else:
                target_sec = 0
            try:
                ts = int(time.time())
                ss_path = os.path.join(session.screenshots_folder, f"{session.member_nickname.lower()}_{ts}.jpg")
                r = subprocess.run(
                    ["ffmpeg", "-loglevel", "error",
                     "-ss", str(target_sec), "-i", final_mp4,
                     "-vframes", "1",
                     "-strict", "unofficial",
                     "-y", ss_path],
                    capture_output=True, timeout=30,
                )
                if r.returncode == 0 and os.path.exists(ss_path):
                    print(f"[manager] Final screenshot captured: {os.path.basename(ss_path)}")
                elif r.returncode != 0:
                    print(f"[manager] Final screenshot failed: {r.stderr.decode(errors='ignore').strip()}")
            except Exception as e:
                print(f"[manager] Screenshot error: {e}")

        if os.path.exists(session.chat_log_path):
            try:
                srt_generator.generate(session.chat_log_path, session.srt_path)
                print(f"[manager] SRT generated: {session.srt_path}")
            except Exception as e:
                print(f"[manager] SRT generation failed: {e}")

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
                "duration_seconds": int(duration),
                "srt_file": os.path.basename(session.srt_path),
                "youtube_id": None,
            }
            with open(session.json_path, "w") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"[manager] JSON metadata: {session.json_path}")
        except Exception as e:
            print(f"[manager] JSON write failed: {e}")

        if remux_ok:
            for fpath in [session.chat_log_path]:
                if os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass

            ffmpeg_log = os.path.splitext(session.output_path)[0].replace(".mp4", "") + ".ffmpeg.log"
            if os.path.exists(ffmpeg_log):
                try:
                    os.remove(ffmpeg_log)
                except Exception:
                    pass

        self.sessions.pop(live_id, None)
        self._stop_events.pop(live_id, None)

        print(f"[manager] Finished recording {session.platform}/{session.member_name}")

    async def shutdown(self):
        for live_id in list(self.sessions.keys()):
            await self._end_session(live_id, reason="interrupted")
        await self.detector.close()
