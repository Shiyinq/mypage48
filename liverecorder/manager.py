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
            await self._end_session(live_id)

    async def check_health(self):
        dead_ids = []
        for live_id, session in self.sessions.items():
            if session.ffmpeg_proc and not stream_recorder.is_running(session.ffmpeg_proc):
                print(f"[manager] ffmpeg died for {live_id}")
                dead_ids.append(live_id)

        for live_id in dead_ids:
            await self._end_session(live_id)

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

        live_folder = os.path.join(recordings_dir, f"{live.platform}_{live.live_id}")
        os.makedirs(live_folder, exist_ok=True)

        base = live.live_id
        mkv_path = os.path.join(live_folder, f"{base}.mkv")
        chat_log_path = os.path.join(live_folder, f"{base}.log")
        srt_path = os.path.join(live_folder, f"{base}.srt")
        json_path = os.path.join(live_folder, f"{base}.json")
        thumbnail_path = os.path.join(live_folder, f"{base}.jpg")

        open(chat_log_path, "w").close()

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
                    recording_start_time,
                    stop_event,
                )
            )
        elif live.platform == "idn" and not live.room_identifier:
            print(f"[manager] No room_identifier for IDN live {live.live_id}, will retry")
            chat_task = asyncio.create_task(
                self._retry_idn_room(
                    live.live_id, live.room_id, live.live_id,
                    chat_log_path, recording_start_time, stop_event,
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
            thumbnail_path=thumbnail_path,
            live_folder=live_folder,
            title=live.title,
            member_image=live.member_image,
            start_at=live.start_at,
            ffmpeg_proc=ffmpeg_proc,
            chat_task=chat_task,
        )

        self.sessions[live.live_id] = session

        asyncio.create_task(self._capture_initial_thumbnail(session))

        print(f"[manager] Started recording {live.platform}/{live.member_name} ({live.live_id})")

    async def _retry_idn_room(
        self, live_id: str, room_id: str, id_live_id: str,
        chat_log_path: str, recording_start_time: float, stop_event: asyncio.Event,
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
                    await chat_capture.capture_idn(rid, chat_log_path, recording_start_time, stop_event)
                except asyncio.CancelledError:
                    pass
                return
            print(f"[manager] Retry room_identifier {attempt}/10 for {live_id} — still null")
        print(f"[manager] Failed to get room_identifier for {live_id} after 10 retries")

    async def _capture_initial_thumbnail(self, session: RecordingSession):
        await asyncio.sleep(30)
        if session.live_id not in self.sessions:
            return
        try:
            subprocess.run(
                ["ffmpeg", "-ss", "30", "-i", session.output_path,
                 "-vframes", "1", "-q:v", "2", "-y", session.thumbnail_path],
                capture_output=True, timeout=15,
            )
        except Exception:
            pass

    async def _end_session(self, live_id: str):
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
                print(f"[manager] Remuxed to MP4: {mp4_path}")
            except Exception as e:
                print(f"[manager] Remux failed: {e}")

        final_mp4 = mp4_path if os.path.exists(mp4_path) else mkv_path
        duration = 0
        if os.path.exists(final_mp4):
            duration = time.time() - session.recording_start_time
            try:
                target_sec = min(max(30, int(duration // 2)), 300)
                subprocess.run(
                    ["ffmpeg", "-ss", str(target_sec), "-i", final_mp4,
                     "-vframes", "1", "-q:v", "2", "-y", session.thumbnail_path],
                    capture_output=True, timeout=30,
                )
            except Exception:
                pass

        if os.path.exists(session.chat_log_path):
            try:
                srt_generator.generate(session.chat_log_path, session.srt_path)
                print(f"[manager] SRT generated: {session.srt_path}")
            except Exception as e:
                print(f"[manager] SRT generation failed: {e}")

        try:
            metadata = {
                "live_id": session.live_id,
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
                "youtube_id": None,
            }
            with open(session.json_path, "w") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"[manager] JSON metadata: {session.json_path}")
        except Exception as e:
            print(f"[manager] JSON write failed: {e}")

        self.sessions.pop(live_id, None)
        self._stop_events.pop(live_id, None)

        print(f"[manager] Finished recording {session.platform}/{session.member_name}")

    async def shutdown(self):
        for live_id in list(self.sessions.keys()):
            await self._end_session(live_id)
        await self.detector.close()
