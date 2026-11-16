"""Evacuate completed local recordings; the service owns the exclusive Drive role."""

import asyncio
import hashlib
import json
import logging
import os
import shutil
import stat
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from random import uniform
from time import monotonic

from ..process_lock import recording_lock
from .archive import (
    MANIFEST_NAME,
    READY_NAME,
    archive_key_for,
    normalize_member_nickname,
    validate_manifest,
)
from .client import (
    DriveAuthorizationError,
    DriveSafetyError,
    authorization_paused,
    validate_filename,
)

log = logging.getLogger("gdrive")


def _snapshot(folder):
    """Include ignored raw files too: reconnects must invalidate cleanup."""
    result = {}
    for path in [folder, *sorted(folder.rglob("*"))]:
        info = path.lstat()
        if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
            raise DriveSafetyError("Source contains a symlink or special file")
        result[str(path.relative_to(folder))] = [
            info.st_dev,
            info.st_ino,
            info.st_mode,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
        ]
    return result


def _metadata(folder):
    candidates = []
    for path in folder.glob("*.json"):
        if path.is_symlink():
            raise DriveSafetyError("Symlink metadata")
        try:
            value = json.loads(path.read_text())
        except (ValueError, UnicodeError):
            continue
        if isinstance(value, dict) and path.name == f"{value.get('live_id')}.json":
            candidates.append((path, value))
    if len(candidates) != 1:
        raise DriveSafetyError("Expected one explicit <live_id>.json metadata file")
    return candidates[0]


def _md5(path):
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _receipt(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".backup-")
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class BackupWorker:
    def __init__(self, config, client):
        self.config = config
        self.client = client
        self._scan_lock = asyncio.Lock()
        self.stop_event = None
        self._retries = {}
        self._missing_mp4_logged = {}
        self._status_lock = threading.Lock()
        self._status = None
        self._idle_since = None

    def _report_idle(self):
        with self._status_lock:
            if self._status != "idle":
                self._idle_since = datetime.now(timezone.utc).isoformat(
                    timespec="seconds"
                )
                self._status = "idle"
                log.info(
                    "Drive backup IDLE: no eligible recording folders to upload; "
                    "idle since %s",
                    self._idle_since,
                )

    def _report_start(self, folder, live_id):
        with self._status_lock:
            self._status = "running"
            log.info(
                "Drive backup START: live_id=%s; folder=%s; last idle since %s",
                live_id,
                folder,
                self._idle_since or "not observed since worker startup",
            )

    def _report_waiting(self):
        with self._status_lock:
            if self._status != "waiting":
                self._status = "waiting"
                log.info("Drive backup WAIT: pending folders need retry or recovery")

    def _is_stopping(self):
        return authorization_paused(self.client) or (
            self.stop_event is not None and self.stop_event.is_set()
        )

    @staticmethod
    def _has_pending_video(folder):
        if (
            folder.is_symlink()
            or not folder.is_dir()
            or not (folder / ".r2_done").is_file()
            or (folder / ".yt_done").exists()
            or (folder / ".abort_upload").exists()
        ):
            return False
        try:
            _, meta = _metadata(folder)
            if meta.get("status") != "completed":
                return False
            video = folder / f"{validate_filename(meta.get('live_id'))}.mp4"
            return video.is_file() and video.stat().st_size > 0
        except (DriveSafetyError, OSError):
            # A malformed source needing review is not an empty queue.
            return True

    async def scan_once(self) -> None:
        if not self.config.backup_to_gdrive or self._is_stopping():
            return
        async with self._scan_lock:
            root = Path(self.config.recordings_dir)
            if root.is_symlink():
                raise DriveSafetyError("Recordings root is a symlink")
            if not root.exists():
                self._report_idle()
                return
            folders = iter(sorted(root.iterdir()))

            async def consume():
                for folder in folders:
                    if self._is_stopping():
                        return
                    if (
                        folder.is_symlink()
                        or not folder.is_dir()
                        or not (folder / ".r2_done").exists()
                        or (folder / ".yt_done").exists()
                    ):
                        continue
                    retry = self._retries.get(folder)
                    if retry is not None and monotonic() < retry[1]:
                        continue
                    # Cancellation cannot leave a background thread deleting sources.
                    task = asyncio.get_running_loop().run_in_executor(
                        executor, self._backup, folder
                    )
                    try:
                        await asyncio.shield(task)
                    except asyncio.CancelledError:
                        await task
                        raise
                    except DriveAuthorizationError:
                        # The shared client logs once and blocks both pipelines.
                        return
                    except Exception as exc:
                        base = min(900, retry[0] * 2 if retry is not None else 15)
                        delay = uniform(base, min(900, base * 1.2))
                        self._retries[folder] = (base, monotonic() + delay)
                        # rmtree can fail after partial deletion. Never describe that
                        # outcome as an intact source or retry from a fresh baseline.
                        log.error(
                            "Drive backup/cleanup failed (%s); "
                            "remaining source preserved: %s; retry in %.1fs",
                            type(exc).__name__,
                            folder,
                            delay,
                        )
                    else:
                        self._retries.pop(folder, None)

            count = max(1, int(self.config.gdrive_max_concurrent_uploads))
            # Backup transfers must not occupy the executor used by Drive replay
            # downloads/control calls, even on a small single-core server.
            with ThreadPoolExecutor(
                max_workers=count, thread_name_prefix="gdrive-backup"
            ) as executor:
                await asyncio.gather(*(consume() for _ in range(count)))
            if self._is_stopping():
                return
            pending = [
                folder for folder in root.iterdir() if self._has_pending_video(folder)
            ]
            if not pending:
                self._report_idle()
            elif any(folder in self._retries for folder in pending):
                self._report_waiting()

    def _backup(self, folder):
        before = _snapshot(folder)
        metadata_path, meta = _metadata(folder)
        live_id = validate_filename(meta.get("live_id"))
        video = folder / f"{live_id}.mp4"
        if not video.is_file() or video.stat().st_size == 0:
            has_parts = any(folder.glob("*.mkv")) or any(folder.glob("*part*.mp4"))
            reason = (
                "raw parts found"
                if has_parts
                else "video missing or empty (possibly a short live)"
            )
            if self._missing_mp4_logged.get(folder) != reason:
                log.info(
                    "No non-empty final MP4 for %s; %s; "
                    "skipping Drive backup and keeping folder on server",
                    live_id,
                    reason,
                )
                self._missing_mp4_logged[folder] = reason
            return
        self._missing_mp4_logged.pop(folder, None)
        key = archive_key_for(folder, meta)
        nickname = normalize_member_nickname(meta.get("member_nickname"))
        receipt_path = Path(self.config.logs_dir) / "gdrive-backups" / f"{key}.json"
        if receipt_path.resolve().is_relative_to(folder.resolve()):
            raise DriveSafetyError("Backup receipt must be outside the source")
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text())
            if (
                not isinstance(receipt, dict)
                or receipt.get("archive_key") != key
                or not isinstance(receipt.get("manifest"), dict)
                or receipt["manifest"].get("source_snapshot") != before
            ):
                raise DriveSafetyError(
                    "Source differs from cleanup receipt; manual review required"
                )

        def recheck():
            if authorization_paused(self.client):
                raise DriveAuthorizationError("Drive authorization paused")
            if (
                (folder / ".abort_upload").exists()
                or not (folder / ".r2_done").is_file()
                or (folder / ".yt_done").exists()
                or _metadata(folder)[1] != meta
                or meta.get("status") != "completed"
                or _snapshot(folder) != before
            ):
                raise DriveSafetyError("Recording changed or is no longer completed")

        recheck()
        assets = [(metadata_path, "metadata"), (video, "video")]
        thumbnail = folder / f"{live_id}_yt_thumb.jpg"
        if thumbnail.exists():
            assets.append((thumbnail, "thumbnail"))
        local = {
            path.name: (role, path.stat().st_size, _md5(path)) for path, role in assets
        }
        recheck()
        self._report_start(folder, live_id)
        self.client.ensure_root()
        archive = self.client.ensure_archive(key, folder.name)
        archive_id = archive["id"]
        children = self.client.list_children(archive_id)
        by_name = {}
        for child in children:
            name = child["name"]
            if name in by_name:
                raise DriveSafetyError("Ambiguous remote archive children")
            by_name[name] = child
        if ".yt_done" in by_name:
            raise DriveSafetyError("Archive already finalized; retain local source")
        previous = None
        if MANIFEST_NAME in by_name:
            previous = validate_manifest(
                self.client.get_json(by_name[MANIFEST_NAME]["id"])
            )
            if any(
                previous.get(field) != expected
                for field, expected in (
                    ("archive_key", key),
                    ("live_id", live_id),
                    ("platform", meta["platform"]),
                    ("recording_folder", folder.name),
                    ("metadata_filename", metadata_path.name),
                )
            ):
                raise DriveSafetyError("Remote manifest identity mismatch")
        ready = {"archive_key": key, "schema_version": 1}
        if READY_NAME in by_name:
            if (
                previous is None
                or self.client.get_json(by_name[READY_NAME]["id"]) != ready
            ):
                raise DriveSafetyError("Invalid remote ready marker")
            manifest = previous
            # A ready archive is immutable. Do not accept a new baseline after
            # reconnect, raw-part changes, or a partially failed local deletion.
            if manifest.get("source_snapshot") != before:
                raise DriveSafetyError(
                    "Ready archive source snapshot differs; manual review required"
                )
        else:
            entries = []
            for path, role in assets:
                remote = self.client.upload_file(archive_id, path)
                entries.append(
                    {
                        "name": path.name,
                        "role": role,
                        "id": remote["id"],
                        "size": int(remote.get("size", -1)),
                        "md5Checksum": remote.get("md5Checksum"),
                    }
                )
            manifest = {
                **(previous or {}),
                "schema_version": 1,
                "archive_key": key,
                "live_id": live_id,
                "platform": meta["platform"],
                "member_nickname": nickname,
                "recording_folder": folder.name,
                "metadata_filename": metadata_path.name,
                "created_at": (previous or {}).get(
                    "created_at", datetime.now(timezone.utc).isoformat()
                ),
                "files": entries,
                "source_snapshot": before,
            }
            for field in ("youtube_id", "youtube_title"):
                if meta.get(field):
                    if manifest.get(field) and manifest[field] != meta[field]:
                        raise DriveSafetyError("Conflicting YouTube checkpoint")
                    manifest[field] = meta[field]
        validate_manifest(manifest)
        if {item["name"] for item in manifest["files"]} != set(local):
            raise DriveSafetyError("Ready archive assets differ from source")
        for item in manifest["files"]:
            role, size, checksum = local[item["name"]]
            remote = self.client.get_file(item["id"])
            if (
                item["role"] != role
                or item["size"] != size
                or item["md5Checksum"].lower() != checksum
                or remote.get("name") != item["name"]
                or archive_id not in remote.get("parents", [])
                or int(remote.get("size", -1)) != size
                or str(remote.get("md5Checksum", "")).lower() != checksum
                or remote.get("trashed", False)
            ):
                raise DriveSafetyError("Remote asset verification failed")
        if meta.get("youtube_id") and manifest.get("youtube_id") != meta["youtube_id"]:
            raise DriveSafetyError("Ready archive lacks local YouTube checkpoint")
        with recording_lock(self.config.logs_dir, live_id):
            recheck()
            publication_attempted = READY_NAME in by_name
            try:
                if not publication_attempted:
                    remote_manifest = self.client.upsert_json(
                        archive_id, MANIFEST_NAME, manifest
                    )
                    if self.client.get_json(remote_manifest["id"]) != manifest:
                        raise DriveSafetyError("Manifest readback failed")
                    recheck()
                    # An API exception can mean the marker committed but its response
                    # was lost. The finally check must cover that case too.
                    publication_attempted = True
                    marker = self.client.upsert_json(archive_id, READY_NAME, ready)
                else:
                    marker = by_name[READY_NAME]
                if self.client.get_json(marker["id"]) != ready:
                    raise DriveSafetyError("Ready marker readback failed")
                recheck()
                _receipt(
                    receipt_path,
                    {
                        **ready,
                        "archive_id": archive_id,
                        "live_id": live_id,
                        "recording_folder": folder.name,
                        "verified_at": datetime.now(timezone.utc).isoformat(),
                        "manifest": manifest,
                    },
                )
            finally:
                if publication_attempted:
                    try:
                        recheck()
                    except (DriveSafetyError, OSError):
                        # No delete-file transport exists. An intentionally invalid
                        # marker quarantines the archive for consumers that validate
                        # readiness rather than checking filename presence alone.
                        log.error("Quarantining stale ready archive %s", key)
                        self.client.upsert_json(
                            archive_id,
                            READY_NAME,
                            {**ready, "schema_version": 0, "quarantined": True},
                        )
                        raise
            recheck()
            shutil.rmtree(folder)
        log.info("Verified Drive backup %s; local source removed", key)
