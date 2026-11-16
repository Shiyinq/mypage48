"""Consume ready Drive archives using the existing YouTube uploader."""

import asyncio
import json
import logging
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from ..models import RecordingSession
from ..notify import notifier
from ..upload import r2_uploader, youtube_uploader
from ..upload.policy import replay_notification_eligible, youtube_queue_key
from .archive import MANIFEST_NAME, READY_NAME, validate_manifest
from .client import DriveAuthorizationError, DriveSafetyError, authorization_paused
from .state import read_json, write_json

log = logging.getLogger("gdrive")
DONE_NAME = ".yt_done"
DISK_MARGIN = 512 * 1024 * 1024
COOLDOWN_LOG_INTERVAL = 6 * 60 * 60


def retention_decision(config, nickname):
    if nickname.strip().casefold() in config.gdrive_keep_members_normalized:
        return {"retention": "keep", "retention_reason": "member_exception"}
    if not config.gdrive_delete_after_youtube_upload:
        return {"retention": "keep", "retention_reason": "deletion_disabled"}
    return {"retention": "delete", "retention_reason": "deletion_enabled"}


def validate_receipt(receipt, key):
    if (
        not isinstance(receipt, dict)
        or type(receipt.get("schema_version")) is not int
        or receipt.get("schema_version") != 1
        or not isinstance(key, str)
        or not re.fullmatch(r"[0-9a-f]{64}", key)
        or receipt.get("archive_key") != key
        or not isinstance(receipt.get("live_id"), str)
        or not receipt["live_id"]
        or not isinstance(receipt.get("member_nickname"), str)
        or not isinstance(receipt.get("completed_at"), str)
        or not isinstance(receipt.get("youtube_id"), str)
        or not receipt["youtube_id"]
        or receipt.get("retention") not in {"keep", "delete"}
        or receipt.get("retention_reason")
        not in {"member_exception", "deletion_disabled", "deletion_enabled"}
        or (receipt["retention"] == "delete")
        != (receipt["retention_reason"] == "deletion_enabled")
    ):
        raise DriveSafetyError("Invalid completion receipt; preserving archive")
    try:
        completed = datetime.fromisoformat(
            receipt["completed_at"].replace("Z", "+00:00")
        )
        if completed.tzinfo is None:
            raise ValueError("Completion time must be timezone-aware")
    except ValueError as exc:
        raise DriveSafetyError("Invalid receipt completion timestamp") from exc
    return receipt


class YouTubeWorker:
    def __init__(self, config, client):
        self.config = config
        self.client = client
        self.state_dir = Path(config.logs_dir) / "gdrive-jobs"
        self.staging = Path(config.recordings_dir).parent / "gdrive-staging"
        self.timing_path = Path(config.logs_dir) / ".gdrive-youtube-timing.json"
        self.cooldown_path = Path(config.logs_dir) / ".youtube_cooldown"
        self._reserved = 0
        self._active = {}
        self._youtube_disabled = False
        self._stopping = False
        self.stop_event = None
        self._recovered_staging = False
        self._cooldown_observed = False
        self._last_cooldown_log = None

    def _job_path(self, key):
        return self.state_dir / f"{key}.json"

    async def _call(self, method, *args, **kwargs):
        return await asyncio.to_thread(method, *args, **kwargs)

    def _blocked(self):
        if (
            self._stopping
            or authorization_paused(self.client)
            or self._youtube_disabled
            or (self.stop_event is not None and self.stop_event.is_set())
        ):
            return True
        if not all(
            (
                self.config.google_client_id,
                self.config.google_client_secret,
                self.config.youtube_refresh_token,
            )
        ):
            return True
        try:
            cooldown = float(self.cooldown_path.read_text())
        except FileNotFoundError:
            cooldown = 0
        now = time.time()
        self._report_cooldown(cooldown, now)
        timing = read_json(self.timing_path)
        return now < max(cooldown, timing.get("next_upload_time", 0))

    def _report_cooldown(self, cooldown, now):
        if now < cooldown:
            self._cooldown_observed = True
            monotonic_now = time.monotonic()
            if (
                self._last_cooldown_log is None
                or monotonic_now - self._last_cooldown_log >= COOLDOWN_LOG_INTERVAL
            ):
                remaining_minutes = max(1, int((cooldown - now + 59) // 60))
                log.info(
                    "YouTube quota cooldown active (%dh %dm remaining); "
                    "Drive-to-YouTube downloads/uploads paused",
                    remaining_minutes // 60,
                    remaining_minutes % 60,
                )
                self._last_cooldown_log = monotonic_now
        elif self._cooldown_observed:
            log.info("YouTube quota cooldown ended; checking Drive-to-YouTube queue")
            self._cooldown_observed = False
            self._last_cooldown_log = None

    async def _children(self, folder):
        children = await self._call(self.client.list_children, folder["id"])
        by_name = {}
        for child in children:
            name = child["name"]
            if name in by_name:
                raise DriveSafetyError("Duplicate archive filenames")
            by_name[name] = child
        return by_name

    async def _load(self, folder):
        key = folder.get("appProperties", {}).get("archive_key")
        if not isinstance(key, str) or not re.fullmatch(r"[0-9a-f]{64}", key):
            raise DriveSafetyError("Invalid archive identity")
        verified = await self._call(self.client.ensure_archive, key, folder["name"])
        if verified["id"] != folder["id"]:
            raise DriveSafetyError("Archive identity mismatch")
        children = await self._children(folder)
        # Check completion before readiness, so malformed receipts never trigger upload.
        if DONE_NAME in children:
            receipt = validate_receipt(
                await self._call(self.client.get_json, children[DONE_NAME]["id"]), key
            )
            self._record_completion(receipt)
            await self._cleanup(folder, receipt)
            return None
        if READY_NAME not in children or MANIFEST_NAME not in children:
            return None
        ready = await self._call(self.client.get_json, children[READY_NAME]["id"])
        manifest = validate_manifest(
            await self._call(self.client.get_json, children[MANIFEST_NAME]["id"])
        )
        if manifest["archive_key"] != key or ready != {
            "schema_version": 1,
            "archive_key": key,
        }:
            raise DriveSafetyError("Ready marker does not match archive")
        # Publication and local deletion are separate API/filesystem operations.
        # Do not consume a published archive until its original source is gone.
        source = Path(self.config.recordings_dir) / manifest["recording_folder"]
        if source.exists() or source.is_symlink():
            return None
        for item in manifest["files"]:
            remote = children.get(item["name"], {})
            if (
                remote.get("id") != item["id"]
                or int(remote.get("size", -1)) != item["size"]
                or remote.get("md5Checksum", "").lower() != item["md5Checksum"].lower()
            ):
                raise DriveSafetyError("Archive assets differ from manifest")
        return manifest

    async def _cleanup(self, folder, receipt):
        key = receipt["archive_key"]
        if receipt["retention"] == "delete":
            current = retention_decision(
                self.config, receipt.get("member_nickname", "")
            )
            if current["retention"] == "keep":
                receipt.update(current)
                await self._call(
                    self.client.upsert_json, folder["id"], DONE_NAME, receipt
                )
            else:
                await self._call(self.client.delete_archive, folder["id"], key)
                log.info("Permanently deleted completed Drive archive %s", key)
        self._remove_staging(key)
        path = self._job_path(key)
        if path.exists():
            path.unlink()

    def _remove_staging(self, key):
        # key has been validated as a SHA-256 archive identity by the caller.
        folder = self.staging / key
        if self.staging.is_symlink() or folder.is_symlink():
            raise DriveSafetyError("Refusing symlink staging cleanup")
        if folder.exists():
            shutil.rmtree(folder)

    async def scan_once(self):
        if authorization_paused(self.client) or not (
            self.config.backup_to_gdrive and self.config.gdrive_to_youtube
        ):
            return
        if not self._recovered_staging:
            if self.staging.is_symlink():
                raise DriveSafetyError("Unsafe staging root")
            if self.staging.exists():
                for stale in self.staging.iterdir():
                    if re.fullmatch(r"[0-9a-f]{64}", stale.name):
                        self._remove_staging(stale.name)
            self._recovered_staging = True
        candidates = []
        for folder in await self._call(self.client.list_archives):
            key = folder.get("appProperties", {}).get("archive_key")
            if key in self._active:
                continue
            try:
                manifest = await self._load(folder)
                if manifest:
                    size = sum(f["size"] for f in manifest["files"])
                    candidates.append((folder, manifest, size))
            except DriveAuthorizationError:
                return
            except Exception as exc:
                log.error(
                    "Drive archive %s needs attention (%s)",
                    folder["id"],
                    type(exc).__name__,
                )
        if self._blocked():
            return
        candidates.sort(
            key=lambda job: youtube_queue_key(
                self.config,
                job[1],
                next(f["size"] for f in job[1]["files"] if f["role"] == "video"),
                job[1]["archive_key"],
            )
        )
        for folder, manifest, size in candidates:
            if (
                self._blocked()
                or len(self._active) >= self.config.max_concurrent_uploads
            ):
                break
            self.staging.mkdir(parents=True, exist_ok=True)
            free = shutil.disk_usage(self.staging).free
            if free < self._reserved + size + DISK_MARGIN:
                log.warning("Insufficient staging space for %s", manifest["live_id"])
                continue
            # No await between reservation and admission: atomic on this loop.
            key = manifest["archive_key"]
            self._reserved += size
            self._active[key] = asyncio.create_task(
                self._process(folder, manifest, size)
            )

    async def close(self):
        self._stopping = True
        # Do not cancel executor transfers: wait for safe checkpoints/cleanup.
        if self._active:
            await asyncio.gather(*list(self._active.values()), return_exceptions=True)

    async def _process(self, folder, manifest, reserved):
        key = manifest["archive_key"]
        try:
            await self._process_inner(folder, manifest)
        except DriveAuthorizationError:
            # Keep durable checkpoints and Drive source; do not retry authorization.
            pass
        except youtube_uploader.QuotaExceededError:
            self.cooldown_path.parent.mkdir(parents=True, exist_ok=True)
            self.cooldown_path.write_text(str(time.time() + 86400))
            # Drive remains authoritative; free media and discard its upload session.
            state = read_json(self._job_path(key))
            state.pop("resume_uri", None)
            state.pop("upload_started", None)
            write_json(self._job_path(key), state)
            self._remove_staging(key)
            log.warning("YouTube quota limit: pausing for 24 hours")
            self._cooldown_observed = True
            self._last_cooldown_log = time.monotonic()
        except youtube_uploader.InvalidGrantError:
            self._youtube_disabled = True
            log.error(
                "YouTube authorization invalid; reauthorize and restart GDrive service"
            )
        except Exception as exc:
            # HTTP exception text may contain authenticated session URLs.
            log.error("Drive-to-YouTube job %s paused (%s)", key, type(exc).__name__)
        finally:
            # The verified Drive archive is authoritative. Never accumulate failed
            # staging copies outside the active-job/disk reservation budget.
            try:
                self._remove_staging(key)
            finally:
                self._reserved -= reserved
                self._active.pop(key, None)

    async def _process_inner(self, folder, manifest):
        key = manifest["archive_key"]
        local = self.staging / key
        if self.staging.is_symlink() or local.is_symlink():
            raise DriveSafetyError("Unsafe staging directory")
        local.mkdir(parents=True, exist_ok=True)
        state = read_json(self._job_path(key))
        if state.get("ambiguous"):
            raise DriveSafetyError(
                "Ambiguous upload result requires manual reconciliation"
            )
        youtube_id = state.get("youtube_id") or manifest.get("youtube_id")
        # A crash before obtaining a resumable URI cannot be safely auto-retried.
        if (
            state.get("upload_started")
            and not youtube_id
            and not state.get("resume_uri")
        ):
            state["ambiguous"] = True
            write_json(self._job_path(key), state)
            raise DriveSafetyError("Upload started without a recoverable session")
        for item in manifest["files"]:
            if youtube_id and item["role"] == "video":
                continue
            destination = local / item["name"]
            await self._call(
                self.client.download_file,
                item["id"],
                destination,
                expected_size=item["size"],
                expected_md5=item["md5Checksum"],
            )
        meta_path = local / manifest["metadata_filename"]
        meta = read_json(meta_path)
        if (
            meta.get("live_id") != manifest["live_id"]
            or meta.get("status") != "completed"
            or (meta.get("member_nickname") or "").strip().casefold()
            != manifest["member_nickname"].strip().casefold()
        ):
            raise DriveSafetyError("Recording metadata does not match archive")
        title = state.get("youtube_title") or manifest.get("youtube_title")
        title = title or youtube_uploader._format_title(meta)

        async def checkpoint(video_id, video_title):
            state.update(youtube_id=video_id, youtube_title=video_title)
            write_json(self._job_path(key), state)
            # Only thumbnail/metadata are needed after a successful video upload.
            (local / f"{manifest['live_id']}.mp4").unlink(missing_ok=True)
            manifest.update(youtube_id=video_id, youtube_title=video_title)
            await self._call(
                self.client.upsert_json, folder["id"], MANIFEST_NAME, manifest
            )

        if youtube_id:
            await checkpoint(youtube_id, title)
        else:
            # Reuse a known remote/local metadata ID instead of uploading a duplicate.
            if meta.get("youtube_id"):
                youtube_id = meta["youtube_id"]
                await checkpoint(youtube_id, meta.get("youtube_title") or title)
            else:
                if self._blocked():
                    return
                session = self._session(local, meta, meta_path)

                def save_uri(uri):
                    state["resume_uri"] = uri
                    write_json(self._job_path(key), state)

                state["upload_started"] = True
                write_json(self._job_path(key), state)
                youtube_id, uri = await youtube_uploader._upload_to_youtube(
                    session,
                    self.config,
                    resume_uri=state.get("resume_uri"),
                    save_uri_callback=save_uri,
                    on_video_uploaded=checkpoint,
                )
                if not youtube_id:
                    if uri:
                        save_uri(uri)
                    raise RuntimeError("YouTube upload incomplete")
        if not state.get("backend_done"):
            ok = await r2_uploader.update_youtube_metadata(
                manifest["live_id"], youtube_id, title, self.config, log
            )
            if not ok:
                raise RuntimeError("Backend finalization incomplete")
            state["backend_done"] = True
            write_json(self._job_path(key), state)
        if not state.get("notification_done"):
            if replay_notification_eligible(self.config, meta):
                ok = await notifier.send_replay_live_notification(
                    manifest["live_id"], title, youtube_id, self.config, str(local)
                )
                if not ok:
                    raise RuntimeError("Replay notification incomplete")
            state["notification_done"] = True
            write_json(self._job_path(key), state)
        receipt = state.get("receipt")
        if receipt is None:
            receipt = {
                "schema_version": 1,
                "archive_key": key,
                "live_id": manifest["live_id"],
                "member_nickname": manifest["member_nickname"],
                "youtube_id": youtube_id,
                "youtube_title": title,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                **retention_decision(self.config, manifest["member_nickname"]),
            }
            # Freeze retention before attempting the remote marker write.
            state["receipt"] = receipt
            write_json(self._job_path(key), state)
        validate_receipt(receipt, key)
        await self._call(self.client.upsert_json, folder["id"], DONE_NAME, receipt)
        self._record_completion(receipt)
        self._remove_staging(key)
        await self._cleanup(folder, receipt)
        log.info("Drive-to-YouTube complete: %s", manifest["live_id"])

    def _record_completion(self, receipt):
        timing = read_json(self.timing_path)
        completed = datetime.fromisoformat(
            receipt["completed_at"].replace("Z", "+00:00")
        )
        deadline = (
            completed.timestamp()
            + max(0, self.config.youtube_upload_delay_minutes) * 60
        )
        timing["next_upload_time"] = max(timing.get("next_upload_time", 0), deadline)
        write_json(self.timing_path, timing)
        self._history(receipt)

    def _history(self, receipt):
        path = Path(self.config.uploads_history_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            for line in path.read_text().splitlines():
                try:
                    if json.loads(line).get("archive_key") == receipt["archive_key"]:
                        return
                except ValueError:
                    continue
        with path.open("a") as stream:
            stream.write(
                json.dumps({**receipt, "uploaded_at": receipt["completed_at"]}) + "\n"
            )

    @staticmethod
    def _session(local, meta, meta_path):
        live_id = meta["live_id"]
        return RecordingSession(
            live_id=live_id,
            platform=meta.get("platform", ""),
            member_name=meta.get("member_name", ""),
            member_nickname=meta.get("member_nickname", ""),
            room_id=meta.get("room_id", ""),
            room_identifier=meta.get("room_identifier"),
            room_url_key=meta.get("room_url_key"),
            hls_url="",
            recording_start_time=0,
            output_path=str(local / f"{live_id}.mp4"),
            chat_log_path="",
            srt_path="",
            json_path=str(meta_path),
            jsonl_path="",
            thumbnail_path="",
            screenshots_folder=str(local / "screenshots"),
            live_folder=str(local),
            title=meta.get("title", ""),
            member_image="",
            start_at=meta.get("start_at", ""),
        )
