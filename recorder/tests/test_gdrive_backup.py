import asyncio
import copy
import hashlib
import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from recorder.src.gdrive.archive import archive_key_for, validate_manifest
from recorder.src.gdrive.backup_worker import BackupWorker
from recorder.src.gdrive.client import DriveSafetyError


class FakeDrive:
    def __init__(self):
        self.files = {}
        self.values = {}
        self.archives = {}
        self.hook = lambda: None
        self.corrupt = False
        self.active = 0
        self.peak = 0
        self.lock = threading.Lock()

    def ensure_root(self):
        return {"id": "root"}

    def ensure_archive(self, key, name):
        return self.archives.setdefault(key, {"id": key, "name": name})

    def list_children(self, parent):
        return [f.copy() for f in self.files.values() if parent in f["parents"]]

    def get_file(self, file_id):
        return self.files[file_id].copy()

    def get_json(self, file_id):
        return copy.deepcopy(self.values[file_id])

    def _put(self, parent, name, payload):
        file_id = f"arbitrary ID {parent} {name}"
        self.files[file_id] = {
            "id": file_id,
            "name": name,
            "parents": [parent],
            "size": str(len(payload)),
            "md5Checksum": hashlib.md5(payload).hexdigest(),
        }
        return self.get_file(file_id)

    def upsert_json(self, parent, name, value):
        result = self._put(parent, name, json.dumps(value).encode())
        self.values[result["id"]] = copy.deepcopy(value)
        return result

    def upload_file(self, parent, local_path, name=None):
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
        try:
            time.sleep(0.005)
            result = self._put(parent, name or local_path.name, local_path.read_bytes())
            self.hook()
            if self.corrupt:
                self.files[result["id"]]["md5Checksum"] = "0" * 32
            return result
        finally:
            with self.lock:
                self.active -= 1


@pytest.fixture
def setup(tmp_path):
    root = tmp_path / "recordings"
    root.mkdir()
    folder = root / "member_123"
    folder.mkdir()
    meta = {
        "live_id": "live123",
        "platform": "showroom",
        "member_nickname": "member",
        "start_at": "2026-01-01T00:00:00Z",
        "status": "completed",
        "youtube_id": "already-uploaded",
        "youtube_title": "Replay",
    }
    (folder / "live123.json").write_text(json.dumps(meta))
    (folder / "live123.mp4").write_bytes(b"final video")
    (folder / "live123_yt_thumb.jpg").write_bytes(b"thumbnail")
    (folder / "raw.part.mkv").write_bytes(b"recovery")
    (folder / ".r2_done").touch()
    config = SimpleNamespace(
        backup_to_gdrive=True,
        gdrive_to_youtube=False,
        recordings_dir=root,
        logs_dir=tmp_path / "logs",
        gdrive_max_concurrent_uploads=2,
        max_concurrent_uploads=1,
    )
    drive = FakeDrive()
    return folder, meta, config, drive


def run(config, drive):
    asyncio.run(BackupWorker(config, drive).scan_once())


@pytest.mark.parametrize("entrypoint", ["scan", "backup"])
def test_mp4_without_r2_completion_never_contacts_drive(setup, monkeypatch, entrypoint):
    folder, meta, config, drive = setup
    (folder / ".r2_done").unlink()
    monkeypatch.setattr(
        drive, "ensure_root", lambda: pytest.fail("Unexpected Drive call")
    )
    worker = BackupWorker(config, drive)
    if entrypoint == "scan":
        asyncio.run(worker.scan_once())
    else:
        with pytest.raises(DriveSafetyError, match="no longer completed"):
            worker._backup(folder)
    assert (folder / "live123.mp4").read_bytes() == b"final video"
    assert (folder / "live123.json").exists()
    assert not drive.archives and not drive.files
    assert not (folder / ".yt_done").exists()


def test_backup_and_receipt(setup):
    folder, meta, config, drive = setup
    key = archive_key_for(folder, meta)
    run(config, drive)
    assert not folder.exists()
    receipt = json.loads(
        (config.logs_dir / "gdrive-backups" / f"{key}.json").read_text()
    )
    manifest = validate_manifest(receipt["manifest"])
    assert manifest["youtube_id"] == "already-uploaded"
    assert manifest["metadata_filename"] == "live123.json"
    assert {f["role"] for f in manifest["files"]} == {"metadata", "video", "thumbnail"}
    assert {f["name"] for f in drive.list_children(key)} == {
        "live123.json",
        "live123.mp4",
        "live123_yt_thumb.jpg",
        "archive_manifest.json",
        ".drive_ready",
    }
    assert drive.get_json(f"arbitrary ID {key} .drive_ready") == {
        "archive_key": key,
        "schema_version": 1,
    }


@pytest.mark.parametrize("has_parts", [False, True])
@pytest.mark.parametrize("empty_mp4", [False, True])
def test_missing_final_video_is_kept_without_drive_calls(
    setup, monkeypatch, caplog, has_parts, empty_mp4
):
    folder, meta, config, drive = setup
    video = folder / "live123.mp4"
    if empty_mp4:
        video.write_bytes(b"")
    else:
        video.unlink()
    if not has_parts:
        (folder / "raw.part.mkv").unlink()
    monkeypatch.setattr(
        drive, "ensure_root", lambda: pytest.fail("Unexpected Drive call")
    )
    caplog.set_level("INFO", logger="gdrive")
    worker = BackupWorker(config, drive)

    async def scan_twice():
        await worker.scan_once()
        await worker.scan_once()

    asyncio.run(scan_twice())
    assert folder.exists()
    assert (folder / "live123.json").exists()
    assert (folder / ".r2_done").exists()
    assert not drive.archives and not drive.files
    messages = [
        r.message for r in caplog.records if "No non-empty final MP4" in r.message
    ]
    assert len(messages) == 1
    assert "keeping folder on server" in messages[0]
    assert ("raw parts found" in messages[0]) == has_parts
    assert not worker._retries


@pytest.mark.parametrize(
    "condition", ["no_mp4", "active", "abort", "yt_done", "symlink", "corrupt"]
)
def test_unsafe_sources_retained(setup, condition, tmp_path):
    folder, meta, config, drive = setup
    if condition == "no_mp4":
        (folder / "live123.mp4").unlink()
    elif condition == "active":
        meta["status"] = "recording"
        (folder / "live123.json").write_text(json.dumps(meta))
    elif condition == "abort":
        (folder / ".abort_upload").touch()
    elif condition == "yt_done":
        (folder / ".yt_done").touch()
    elif condition == "symlink":
        target = tmp_path / "outside"
        target.write_text("safe")
        (folder / "link").symlink_to(target)
    else:
        drive.corrupt = True
    run(config, drive)
    assert folder.exists()
    assert (folder / "raw.part.mkv").exists()
    assert not any(f["name"] == ".drive_ready" for f in drive.files.values())


@pytest.mark.parametrize("change", ["metadata", "raw", "abort", "new_file"])
def test_changes_during_upload_never_ready(setup, change):
    folder, meta, config, drive = setup

    def mutate():
        if change == "metadata":
            meta["status"] = "recording"
            (folder / "live123.json").write_text(json.dumps(meta))
        elif change == "raw":
            (folder / "raw.part.mkv").write_bytes(b"new raw content")
        elif change == "abort":
            (folder / ".abort_upload").touch()
        else:
            (folder / "new.part").touch()

    drive.hook = mutate
    run(config, drive)
    assert folder.exists()
    assert not any(f["name"] == ".drive_ready" for f in drive.files.values())


def test_receipt_failure_retains_source_and_ready_retry(setup, monkeypatch):
    folder, meta, config, drive = setup
    from recorder.src.gdrive import backup_worker

    original = backup_worker._receipt

    def fail(*args):
        raise OSError("disk full")

    monkeypatch.setattr(backup_worker, "_receipt", fail)
    run(config, drive)
    assert folder.exists()
    assert any(f["name"] == ".drive_ready" for f in drive.files.values())
    monkeypatch.setattr(backup_worker, "_receipt", original)
    drive.hook = lambda: pytest.fail("Ready archives must not be rewritten")
    run(config, drive)
    assert not folder.exists()


def test_bounded_scans(setup):
    folder, meta, config, drive = setup
    import shutil

    for number in range(5):
        shutil.copytree(folder, folder.parent / f"other_{number}")
    run(config, drive)
    assert drive.peak == 2
    assert list(folder.parent.iterdir()) == []


def test_archive_identity(setup):
    folder, meta, _, _ = setup
    key = archive_key_for(folder, meta)
    assert key == archive_key_for(Path("/different/root") / folder.name, meta)
    assert key != archive_key_for(folder, {**meta, "platform": "idn"})
    assert key != archive_key_for(folder, {**meta, "start_at": "other"})


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "../escape"),
        ("name", "a\\b"),
        ("id", ""),
        ("role", "unknown"),
        ("size", True),
        ("size", -1),
        ("md5Checksum", "not-a-checksum"),
    ],
)
def test_manifest_rejects_invalid_entries(setup, field, value):
    _, _, config, drive = setup
    run(config, drive)
    manifest = next(v for v in drive.values.values() if "files" in v)
    manifest = copy.deepcopy(manifest)
    manifest["files"][0][field] = value
    with pytest.raises(DriveSafetyError):
        validate_manifest(manifest)


def test_existing_youtube_checkpoint_preserved(setup):
    folder, meta, config, drive = setup
    key = archive_key_for(folder, meta)
    # Build a valid but incomplete archive, as after a process interruption.
    from unittest.mock import patch

    from recorder.src.gdrive import backup_worker

    with patch.object(backup_worker, "_receipt", side_effect=OSError("disk full")):
        run(config, drive)
    ready_id = f"arbitrary ID {key} .drive_ready"
    del drive.files[ready_id]
    del drive.values[ready_id]
    manifest_id = f"arbitrary ID {key} archive_manifest.json"
    drive.values[manifest_id]["youtube_id"] = "remote-checkpoint"
    meta.pop("youtube_id")
    meta.pop("youtube_title")
    (folder / "live123.json").write_text(json.dumps(meta))
    run(config, drive)
    assert not folder.exists()
    assert drive.values[manifest_id]["youtube_id"] == "remote-checkpoint"


def test_change_after_receipt_prevents_cleanup(setup, monkeypatch):
    folder, _, config, drive = setup
    from recorder.src.gdrive import backup_worker

    original = backup_worker._receipt

    def mutate(path, value):
        original(path, value)
        (folder / ".abort_upload").touch()

    monkeypatch.setattr(backup_worker, "_receipt", mutate)
    run(config, drive)
    assert folder.exists()
    assert (folder / "raw.part.mkv").exists()


def test_disabled_worker(setup):
    folder, _, config, drive = setup
    config.backup_to_gdrive = False
    run(config, drive)
    assert folder.exists()
    assert not drive.files


@pytest.mark.parametrize("nickname", [None, "", "   ", "missing"])
def test_optional_nickname_preserves_metadata(setup, nickname):
    folder, meta, config, drive = setup
    if nickname == "missing":
        meta.pop("member_nickname")
    else:
        meta["member_nickname"] = nickname
    metadata_path = folder / "live123.json"
    metadata_path.write_text(json.dumps(meta, indent=3))
    original = metadata_path.read_bytes()
    key = archive_key_for(folder, meta)
    run(config, drive)
    assert not folder.exists()
    manifest = drive.get_json(f"arbitrary ID {key} archive_manifest.json")
    assert validate_manifest(manifest)["member_nickname"] == ""
    metadata = next(f for f in manifest["files"] if f["role"] == "metadata")
    assert metadata["name"] == "live123.json"
    assert metadata["md5Checksum"] == hashlib.md5(original).hexdigest()
    assert archive_key_for(folder, meta) == key


@pytest.mark.parametrize("phase", ["manifest", "ready", "ready_lost_response"])
@pytest.mark.parametrize("change", ["reconnect", "video", "raw"])
def test_publication_source_races(setup, monkeypatch, phase, change):
    folder, meta, config, drive = setup
    key = archive_key_for(folder, meta)
    original = drive.upsert_json

    def publish(parent, name, value):
        result = original(parent, name, value)
        target = "archive_manifest.json" if phase == "manifest" else ".drive_ready"
        if name == target and value.get("schema_version") == 1:
            if change == "reconnect":
                meta["status"] = "recording"
                (folder / "live123.json").write_text(json.dumps(meta))
                (folder / ".abort_upload").touch()
            else:
                filename = "live123.mp4" if change == "video" else "raw.part.mkv"
                (folder / filename).write_bytes(b"changed during publication")
            if phase == "ready_lost_response":
                raise OSError("response lost after Drive committed")
        return result

    monkeypatch.setattr(drive, "upsert_json", publish)
    run(config, drive)
    assert folder.exists()
    assert (folder / "raw.part.mkv").exists()
    marker_id = f"arbitrary ID {key} .drive_ready"
    if phase == "manifest":
        assert marker_id not in drive.values
    else:
        assert drive.values[marker_id]["schema_version"] == 0
        assert drive.values[marker_id]["quarantined"] is True
    assert not (config.logs_dir / "gdrive-backups" / f"{key}.json").exists()


@pytest.mark.parametrize("with_receipt", [False, True])
def test_cleanup_retry_rejects_new_raw_baseline(setup, monkeypatch, with_receipt):
    folder, _, config, drive = setup
    from recorder.src.gdrive import backup_worker

    if with_receipt:

        def fail(*args):
            raise OSError("cleanup failed before removing anything")

        monkeypatch.setattr(backup_worker.shutil, "rmtree", fail)
    else:

        def fail(*args):
            raise OSError("receipt disk full")

        monkeypatch.setattr(backup_worker, "_receipt", fail)
    run(config, drive)
    assert folder.exists()
    monkeypatch.undo()
    (folder / "raw.part.mkv").write_bytes(b"reconnected recording data")
    run(config, drive)
    assert folder.exists()
    assert (folder / "raw.part.mkv").read_bytes() == b"reconnected recording data"


def test_backup_only_retry_reverifies_remote(setup, monkeypatch):
    folder, meta, config, drive = setup
    from recorder.src.gdrive import backup_worker

    def fail(*args):
        raise OSError("receipt disk full")

    monkeypatch.setattr(backup_worker, "_receipt", fail)
    run(config, drive)
    assert folder.exists()
    monkeypatch.undo()
    key = archive_key_for(folder, meta)
    drive.files[f"arbitrary ID {key} live123.mp4"]["md5Checksum"] = "0" * 32
    assert config.gdrive_to_youtube is False
    run(config, drive)
    assert folder.exists()
    assert not (config.logs_dir / "gdrive-backups" / f"{key}.json").exists()


def test_partial_cleanup_failure_is_not_rebaselined(setup, monkeypatch):
    folder, _, config, drive = setup
    from recorder.src.gdrive import backup_worker

    def partially_delete(path):
        (path / "raw.part.mkv").unlink()
        raise OSError("partial cleanup failure")

    monkeypatch.setattr(backup_worker.shutil, "rmtree", partially_delete)
    run(config, drive)
    assert folder.exists()
    monkeypatch.undo()
    run(config, drive)
    assert folder.exists()
    assert (folder / "live123.mp4").exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("live_id", "../bad"),
        ("platform", ""),
        ("start_at", {"bad": "identity"}),
        ("recording_started_at", 123),
    ],
)
def test_invalid_recording_identity_rejected(setup, field, value):
    folder, meta, _, _ = setup
    with pytest.raises(DriveSafetyError):
        archive_key_for(folder, {**meta, field: value})


def test_ready_response_lost_with_stable_source_is_retryable(setup, monkeypatch):
    folder, _, config, drive = setup
    original = drive.upsert_json

    def publish(parent, name, value):
        result = original(parent, name, value)
        if name == ".drive_ready":
            raise OSError("response lost")
        return result

    monkeypatch.setattr(drive, "upsert_json", publish)
    run(config, drive)
    assert folder.exists()
    monkeypatch.undo()
    drive.hook = lambda: pytest.fail("Do not rewrite a ready archive")
    run(config, drive)
    assert not folder.exists()


def test_manifest_missing_nickname_normalizes_empty(setup):
    _, _, config, drive = setup
    run(config, drive)
    manifest = next(v for v in drive.values.values() if "files" in v)
    manifest = copy.deepcopy(manifest)
    manifest.pop("member_nickname")
    assert validate_manifest(manifest)["member_nickname"] == ""
    assert "member_nickname" not in manifest


def test_ready_retry_rejects_manifest_identity_mismatch(setup, monkeypatch):
    folder, meta, config, drive = setup
    from recorder.src.gdrive import backup_worker

    def fail(*args):
        raise OSError("receipt disk full")

    monkeypatch.setattr(backup_worker, "_receipt", fail)
    run(config, drive)
    monkeypatch.undo()
    key = archive_key_for(folder, meta)
    drive.values[f"arbitrary ID {key} archive_manifest.json"]["platform"] = "idn"
    run(config, drive)
    assert folder.exists()
    assert not (config.logs_dir / "gdrive-backups" / f"{key}.json").exists()


def test_recording_lock_covers_only_finalization(setup, monkeypatch):
    import fcntl

    from recorder.src.gdrive import backup_worker
    from recorder.src.process_lock import recording_lock_name

    folder, meta, config, drive = setup
    claims = config.logs_dir / "gdrive-claims"
    claims.mkdir(parents=True)
    lock_path = claims / recording_lock_name(meta["live_id"])
    phases = []

    def check_lock(expected, phase):
        with lock_path.open("a") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                held = True
            else:
                held = False
                fcntl.flock(stream, fcntl.LOCK_UN)
        assert held is expected
        phases.append(phase)

    drive.hook = lambda: check_lock(False, "upload")
    original_publish = drive.upsert_json
    original_receipt = backup_worker._receipt
    original_delete = backup_worker.shutil.rmtree

    def publish(*args):
        check_lock(True, "publication")
        return original_publish(*args)

    def receipt(*args):
        check_lock(True, "receipt")
        return original_receipt(*args)

    def delete(*args):
        check_lock(True, "cleanup")
        return original_delete(*args)

    monkeypatch.setattr(drive, "upsert_json", publish)
    monkeypatch.setattr(backup_worker, "_receipt", receipt)
    monkeypatch.setattr(backup_worker.shutil, "rmtree", delete)
    run(config, drive)
    assert not folder.exists()
    assert set(phases) == {"upload", "publication", "receipt", "cleanup"}
    check_lock(False, "released")


def test_reconnect_while_waiting_for_final_lock_aborts_publication(setup):
    from concurrent.futures import ThreadPoolExecutor

    from recorder.src.process_lock import recording_lock

    folder, meta, config, drive = setup
    uploaded = threading.Event()
    upload_count = 0

    def upload_finished():
        nonlocal upload_count
        upload_count += 1
        if upload_count == 3:
            uploaded.set()

    drive.hook = upload_finished
    with ThreadPoolExecutor(max_workers=1) as executor:
        with recording_lock(config.logs_dir, meta["live_id"]):
            job = executor.submit(BackupWorker(config, drive)._backup, folder)
            assert uploaded.wait(timeout=5)
            assert not any(f["name"] == ".drive_ready" for f in drive.files.values())
            meta["status"] = "recording"
            (folder / "live123.json").write_text(json.dumps(meta))
            (folder / ".abort_upload").touch()
        with pytest.raises(DriveSafetyError):
            job.result(timeout=5)
    assert folder.exists()
    assert not any(f["name"] == ".drive_ready" for f in drive.files.values())


def test_failure_logging_does_not_expose_exception_details(setup, caplog):
    folder, _, config, drive = setup
    secret = "https://upload.example/resumable?upload_id=SECRET_TOKEN"

    def fail():
        raise OSError(secret)

    drive.hook = fail
    run(config, drive)
    assert folder.exists()
    assert "OSError" in caplog.text
    assert secret not in caplog.text
    assert "SECRET_TOKEN" not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)


@pytest.mark.parametrize("concurrency", [1, 2])
def test_shutdown_finishes_active_backups_without_new_admission(setup, concurrency):
    import shutil

    folder, _, config, drive = setup
    config.gdrive_max_concurrent_uploads = concurrency
    for number in range(3):
        shutil.copytree(folder, folder.parent / f"pending_{number}")
    active_started = threading.Event()
    release = threading.Event()
    entered = 0
    guard = threading.Lock()

    def pause_upload():
        nonlocal entered
        with guard:
            entered += 1
            if entered == concurrency:
                active_started.set()
        if not release.wait(timeout=5):
            raise TimeoutError("Test did not release active backups")

    drive.hook = pause_upload

    async def scenario():
        worker = BackupWorker(config, drive)
        worker.stop_event = asyncio.Event()
        scan = asyncio.create_task(worker.scan_once())
        try:
            assert await asyncio.to_thread(active_started.wait, 5)
            worker.stop_event.set()
            assert not scan.done()
        finally:
            release.set()
            await asyncio.wait_for(scan, timeout=5)
        await worker.scan_once()

    asyncio.run(scenario())
    assert len(drive.archives) == concurrency
    assert len(list(folder.parent.iterdir())) == 4 - concurrency
    assert len(list((config.logs_dir / "gdrive-backups").glob("*.json"))) == concurrency


def test_shutdown_before_scan_admits_nothing(setup):
    folder, _, config, drive = setup
    worker = BackupWorker(config, drive)
    worker.stop_event = threading.Event()
    worker.stop_event.set()
    asyncio.run(worker.scan_once())
    assert folder.exists()
    assert not drive.archives


@pytest.mark.parametrize("upper_jitter", [False, True])
def test_retry_backoff_deadlines_exponential_jitter_and_cap(
    setup, monkeypatch, upper_jitter
):
    from recorder.src.gdrive import backup_worker

    folder, _, config, drive = setup
    worker = BackupWorker(config, drive)
    now = [1000.0]
    attempts = []
    jitter_ranges = []

    def fail(path):
        attempts.append(path)
        raise DriveSafetyError("Permanent failure")

    def jitter(low, high):
        jitter_ranges.append((low, high))
        return high if upper_jitter else low

    monkeypatch.setattr(worker, "_backup", fail)
    monkeypatch.setattr(backup_worker, "monotonic", lambda: now[0])
    monkeypatch.setattr(backup_worker, "uniform", jitter)

    async def scenario():
        for attempt, base in enumerate([15, 30, 60, 120, 240, 480, 900, 900], 1):
            await worker.scan_once()
            assert len(attempts) == attempt
            low, high = jitter_ranges[-1]
            assert low == base
            assert high == min(900, base * 1.2)
            delay = high if upper_jitter else low
            assert worker._retries[folder] == (base, now[0] + delay)
            now[0] += delay - 0.01
            await worker.scan_once()
            assert len(attempts) == attempt
            now[0] = worker._retries[folder][1]

    asyncio.run(scenario())
    assert folder.exists()


def test_retry_is_per_folder_and_success_clears_state(setup, monkeypatch):
    import shutil

    from recorder.src.gdrive import backup_worker

    folder, _, config, drive = setup
    other = folder.parent / "other"
    shutil.copytree(folder, other)
    worker = BackupWorker(config, drive)
    now = [1000.0]
    attempts = []
    failing = {folder}

    def backup(path):
        attempts.append(path)
        if path in failing:
            raise OSError("Failure")

    monkeypatch.setattr(worker, "_backup", backup)
    monkeypatch.setattr(backup_worker, "monotonic", lambda: now[0])
    monkeypatch.setattr(backup_worker, "uniform", lambda low, high: low)

    async def scenario():
        await worker.scan_once()
        assert attempts.count(folder) == 1
        assert attempts.count(other) == 1
        await worker.scan_once()
        assert attempts.count(folder) == 1
        assert attempts.count(other) == 2
        assert other not in worker._retries
        now[0] = worker._retries[folder][1]
        failing.clear()
        await worker.scan_once()
        assert attempts.count(folder) == 2
        assert folder not in worker._retries
        failing.add(folder)
        await worker.scan_once()
        assert worker._retries[folder] == (15, now[0] + 15)

    asyncio.run(scenario())


def test_upload_failure_retains_source(setup):
    folder, _, config, drive = setup

    def fail():
        raise OSError("network unavailable")

    drive.hook = fail
    run(config, drive)
    assert folder.exists()
    assert not any(f["name"] == ".drive_ready" for f in drive.files.values())
