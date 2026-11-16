"""Offline contracts for BackupWorker's transition-based gdrive status logs."""

import asyncio
import copy
import hashlib
import json
import logging
import threading
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from recorder.src.gdrive.backup_worker import BackupWorker

IDLE = "Drive backup IDLE: no eligible recording folders to upload; idle since %s"
START = "Drive backup START: live_id=%s; folder=%s; last idle since %s"


class FakeDrive:
    """Store tiny verified assets, with hooks at the first real Drive call."""

    def __init__(self):
        self.authorization_failed = False
        self.calls = []
        self.files = {}
        self.values = {}
        self.lock = threading.RLock()
        self.on_root = lambda: None

    def ensure_root(self):
        with self.lock:
            self.calls.append("ensure_root")
        self.on_root()
        return {"id": "root"}

    def ensure_archive(self, key, name):
        return {"id": key, "name": name}

    def list_children(self, parent):
        with self.lock:
            return [
                item.copy() for item in self.files.values() if parent in item["parents"]
            ]

    def get_file(self, file_id):
        with self.lock:
            return self.files[file_id].copy()

    def get_json(self, file_id):
        with self.lock:
            return copy.deepcopy(self.values[file_id])

    def _put(self, parent, name, payload):
        file_id = f"{parent}/{name}"
        with self.lock:
            self.files[file_id] = {
                "id": file_id,
                "name": name,
                "parents": [parent],
                "size": str(len(payload)),
                "md5Checksum": hashlib.md5(payload, usedforsecurity=False).hexdigest(),
            }
            return self.files[file_id].copy()

    def upload_file(self, parent, path):
        return self._put(parent, path.name, path.read_bytes())

    def upsert_json(self, parent, name, value):
        with self.lock:
            result = self._put(parent, name, json.dumps(value).encode())
            self.values[result["id"]] = copy.deepcopy(value)
            return result


@pytest.fixture
def setup(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    config = SimpleNamespace(
        backup_to_gdrive=True,
        gdrive_to_youtube=False,
        recordings_dir=tmp_path / "recordings",
        logs_dir=tmp_path / "logs",
        gdrive_max_concurrent_uploads=2,
        max_concurrent_uploads=1,
    )
    drive = FakeDrive()
    return BackupWorker(config, drive), drive


def recording(worker, live_id="live123", *, r2=True, status="completed", video=b"mp4"):
    folder = worker.config.recordings_dir / f"member_{live_id}"
    folder.mkdir(parents=True)
    (folder / f"{live_id}.json").write_text(
        json.dumps(
            {
                "live_id": live_id,
                "platform": "showroom",
                "member_nickname": "member",
                "start_at": "2026-01-01T00:00:00Z",
                "status": status,
            }
        )
    )
    if video is not None:
        (folder / f"{live_id}.mp4").write_bytes(video)
    if r2:
        (folder / ".r2_done").touch()
    return folder


def statuses(caplog):
    records = [
        record
        for record in caplog.records
        if record.getMessage().startswith(
            ("Drive backup IDLE:", "Drive backup START:", "Drive backup WAIT:")
        )
    ]
    assert all(record.name == "gdrive" for record in records)
    assert all(record.levelno == logging.INFO for record in records)
    return records


def kinds(caplog):
    return [
        record.getMessage().split(":", 1)[0].split()[-1] for record in statuses(caplog)
    ]


def assert_idle(record):
    assert record.msg == IDLE
    assert len(record.args) == 1
    value = record.args[0]
    stamp = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    assert stamp.utcoffset() == timedelta(0)
    assert abs(datetime.now(timezone.utc) - stamp) < timedelta(minutes=1)
    return value


def assert_start(record, folder, live_id, idle_since):
    assert record.msg == START
    assert record.args[0] == live_id
    assert str(record.args[1]) == str(folder)
    assert str(record.args[2]) == str(idle_since)


@pytest.mark.parametrize("existing_root", [False, True])
def test_empty_scan_reports_idle_once_then_real_backup_starts_and_returns_idle(
    setup, caplog, existing_root
):
    worker, drive = setup
    if existing_root:
        worker.config.recordings_dir.mkdir()

    async def scenario():
        await worker.scan_once()
        assert kinds(caplog) == ["IDLE"]
        idle_since = assert_idle(statuses(caplog)[0])
        await worker.scan_once()
        assert kinds(caplog) == ["IDLE"]
        assert drive.calls == []
        folder = recording(worker)

        def first_drive_call():
            assert kinds(caplog) == ["IDLE", "START"]
            assert_start(statuses(caplog)[1], folder, "live123", idle_since)

        drive.on_root = first_drive_call
        await worker.scan_once()
        assert not folder.exists()
        assert drive.calls == ["ensure_root"]
        assert kinds(caplog) == ["IDLE", "START", "IDLE"]
        assert_idle(statuses(caplog)[-1])
        await worker.scan_once()
        assert kinds(caplog) == ["IDLE", "START", "IDLE"]

    asyncio.run(scenario())


@pytest.mark.parametrize("source", ["raw", "missing", "empty", "live", "no_r2"])
def test_ineligible_sources_remain_idle_without_start_or_drive_calls(
    setup, caplog, source
):
    worker, drive = setup
    folder = recording(
        worker,
        r2=source != "no_r2",
        status="recording" if source == "live" else "completed",
        video=None
        if source in {"raw", "missing"}
        else b""
        if source == "empty"
        else b"mp4",
    )
    if source == "raw":
        (folder / "raw.part.mkv").write_bytes(b"raw")

    async def scenario():
        await worker.scan_once()
        await worker.scan_once()

    asyncio.run(scenario())
    assert folder.exists()
    assert drive.calls == []
    assert kinds(caplog) == ["IDLE"]
    assert_idle(statuses(caplog)[0])


def test_retry_reports_wait_not_idle_and_backoff_does_not_restart(setup, caplog):
    worker, drive = setup

    async def scenario():
        await worker.scan_once()
        assert kinds(caplog) == ["IDLE"]
        idle_since = assert_idle(statuses(caplog)[0])
        folder = recording(worker)

        def fail():
            assert_start(statuses(caplog)[-1], folder, "live123", idle_since)
            raise OSError("temporary transport failure")

        drive.on_root = fail
        await worker.scan_once()
        assert folder.exists()
        assert kinds(caplog) == ["IDLE", "START", "WAIT"]
        await worker.scan_once()
        assert kinds(caplog) == ["IDLE", "START", "WAIT"]
        assert drive.calls == ["ensure_root"]
        # Admit the retry without sleeping or depending on jitter.
        base, _ = worker._retries[folder]
        worker._retries[folder] = (base, 0)
        drive.on_root = lambda: None
        await worker.scan_once()
        assert not folder.exists()
        assert kinds(caplog) == ["IDLE", "START", "WAIT", "START", "IDLE"]

    asyncio.run(scenario())


@pytest.mark.parametrize("mode", ["disabled", "stopped", "auth_paused"])
@pytest.mark.parametrize("with_source", [False, True])
def test_inactive_worker_emits_no_normal_status(setup, caplog, mode, with_source):
    worker, drive = setup
    if with_source:
        recording(worker)
    if mode == "disabled":
        worker.config.backup_to_gdrive = False
    elif mode == "auth_paused":
        drive.authorization_failed = True
    else:
        worker.stop_event = asyncio.Event()
        worker.stop_event.set()
    asyncio.run(worker.scan_once())
    assert statuses(caplog) == []
    assert drive.calls == []


def test_wait_returns_to_idle_if_pending_source_disappears(setup, caplog):
    worker, drive = setup
    folder = recording(worker)

    def fail():
        raise OSError("temporary transport failure")

    drive.on_root = fail

    async def scenario():
        await worker.scan_once()
        assert kinds(caplog) == ["START", "WAIT"]
        # A source removed by another pipeline must not keep a stale WAIT state.
        for path in folder.iterdir():
            path.unlink()
        folder.rmdir()
        await worker.scan_once()
        assert kinds(caplog) == ["START", "WAIT", "IDLE"]
        assert_idle(statuses(caplog)[-1])
        await worker.scan_once()
        assert kinds(caplog) == ["START", "WAIT", "IDLE"]
        assert drive.calls == ["ensure_root"]

    asyncio.run(scenario())


def test_parallel_real_transfers_log_each_start_and_idle_only_after_both_finish(
    setup, caplog
):
    worker, drive = setup
    both_started = threading.Event()
    release = threading.Event()
    admitted = []

    def hold_transfers():
        with drive.lock:
            admitted.append(threading.get_ident())
            if len(admitted) == 2:
                both_started.set()
        if not release.wait(5):
            raise TimeoutError("test did not release parallel transfers")

    async def scenario():
        await worker.scan_once()
        assert kinds(caplog) == ["IDLE"]
        idle_since = assert_idle(statuses(caplog)[0])
        folders = {
            "live123": recording(worker),
            "live456": recording(worker, "live456"),
        }
        drive.on_root = hold_transfers
        scan = asyncio.create_task(worker.scan_once())
        try:
            assert await asyncio.to_thread(both_started.wait, 5)
            assert len(set(admitted)) == 2
            assert kinds(caplog) == ["IDLE", "START", "START"]
            starts = statuses(caplog)[1:]
            assert {record.args[0] for record in starts} == set(folders)
            for record in starts:
                assert_start(
                    record, folders[record.args[0]], record.args[0], idle_since
                )
        finally:
            release.set()
            await asyncio.wait_for(scan, 10)
        assert all(not folder.exists() for folder in folders.values())
        assert kinds(caplog) == ["IDLE", "START", "START", "IDLE"]
        assert_idle(statuses(caplog)[-1])

    asyncio.run(scenario())
