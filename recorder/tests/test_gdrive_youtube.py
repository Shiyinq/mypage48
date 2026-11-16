"""Offline contract tests for Drive-backed YouTube scheduling and recovery."""

import asyncio
import copy
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from googleapiclient.errors import HttpError
from httplib2 import Response

from recorder.src.gdrive import youtube_worker
from recorder.src.gdrive.archive import MANIFEST_NAME, READY_NAME
from recorder.src.gdrive.client import DriveSafetyError, validate_filename
from recorder.src.gdrive.state import read_json, write_json
from recorder.src.gdrive.youtube_worker import DONE_NAME, YouTubeWorker
from recorder.src.upload import youtube_uploader


class MemoryDrive:
    """Drive-shaped storage; only downloads write media into temporary staging."""

    def __init__(self):
        self.archives = {}
        self.files = {}
        self.payloads = {}
        self.calls = []

    def put(self, parent, name, payload):
        file_id = f"{parent}/{name}"
        item = {
            "id": file_id,
            "name": name,
            "size": str(len(payload)),
            "md5Checksum": hashlib.md5(payload).hexdigest(),
            "parent": parent,
        }
        self.files[file_id] = item
        self.payloads[file_id] = payload
        return copy.deepcopy(item)

    def upsert_json(self, parent, name, value):
        self.calls.append(("write", parent, name))
        return self.put(parent, name, json.dumps(value).encode())

    def get_json(self, file_id):
        self.calls.append(("json", file_id))
        return json.loads(self.payloads[file_id])

    def list_archives(self):
        self.calls.append(("list",))
        return copy.deepcopy(list(self.archives.values()))

    def get_archive(self, archive_id, key):
        self.calls.append(("get", archive_id, key))
        if archive_id not in self.archives:
            raise HttpError(
                Response({"status": "404"}), b'{"error":{"message":"File not found"}}'
            )
        archive = self.archives[archive_id]
        validate_filename(archive["name"])
        if (
            archive["id"] == "root"
            or archive.get("mimeType") != "application/vnd.google-apps.folder"
            or archive.get("parents") != ["root"]
            or archive.get("trashed", False)
            or archive.get("shared") is not False
            or archive.get("ownedByMe") is not True
            or archive["appProperties"].get("app") != "mypage48"
            or archive["appProperties"].get("role") != "archive"
            or archive["appProperties"].get("archive_key") != key
        ):
            raise DriveSafetyError("Not a private managed archive")
        return copy.deepcopy(archive)

    def list_children(self, parent):
        self.calls.append(("children", parent))
        return copy.deepcopy(
            [item for item in self.files.values() if item["parent"] == parent]
        )

    def download_file(self, file_id, destination, *, expected_size, expected_md5):
        self.calls.append(("download", file_id))
        payload = self.payloads[file_id]
        assert len(payload) == expected_size
        assert hashlib.md5(payload).hexdigest() == expected_md5
        destination.write_bytes(payload)

    def delete_archive(self, parent, key):
        # The worker must commit a valid completion receipt before permanent delete.
        receipt = self.get_json(f"{parent}/{DONE_NAME}")
        assert receipt["archive_key"] == key
        assert receipt["youtube_id"]
        assert receipt["retention"] == "delete"
        self.calls.append(("delete", parent, key))
        del self.archives[parent]
        for file_id in list(self.files):
            if self.files[file_id]["parent"] == parent:
                del self.files[file_id]
                del self.payloads[file_id]

    def add_archive(self, live_id="live1", nickname="Erine", size=20):
        key = hashlib.sha256(live_id.encode()).hexdigest()
        self.archives[key] = {
            "id": key,
            "name": live_id,
            "appProperties": {"app": "mypage48", "role": "archive", "archive_key": key},
            "mimeType": "application/vnd.google-apps.folder",
            "parents": ["root"],
            "shared": False,
            "ownedByMe": True,
        }
        meta = {
            "live_id": live_id,
            "platform": "showroom",
            "status": "completed",
            "member_nickname": nickname,
            "title": "Replay",
            "live_type": "public",
        }
        files = []
        for name, role, payload in [
            (f"{live_id}.mp4", "video", b"v" * size),
            (f"{live_id}.json", "metadata", json.dumps(meta).encode()),
        ]:
            item = self.put(key, name, payload)
            files.append(
                {
                    "name": name,
                    "role": role,
                    "id": item["id"],
                    "size": len(payload),
                    "md5Checksum": item["md5Checksum"],
                }
            )
        manifest = {
            "schema_version": 1,
            "archive_key": key,
            "live_id": live_id,
            "platform": "showroom",
            "recording_folder": live_id,
            "member_nickname": nickname,
            "metadata_filename": f"{live_id}.json",
            "files": files,
        }
        self.upsert_json(key, MANIFEST_NAME, manifest)
        self.upsert_json(key, READY_NAME, {"schema_version": 1, "archive_key": key})
        return key


@pytest.fixture
def harness(tmp_path, monkeypatch):
    config = SimpleNamespace(
        backup_to_gdrive=True,
        gdrive_to_youtube=True,
        gdrive_delete_after_youtube_upload=False,
        gdrive_keep_members_normalized=set(),
        youtube_upload_priority_ranks={"erine": 0},
        recordings_dir=tmp_path / "recordings",
        logs_dir=tmp_path / "logs",
        uploads_history_path=tmp_path / "logs" / "uploads.jsonl",
        max_concurrent_uploads=1,
        google_client_id="client",
        google_client_secret="secret",
        youtube_refresh_token="token",
        youtube_upload_delay_minutes=0,
        youtube_privacy_status="public",
    )
    drive = MemoryDrive()

    async def upload(
        session, config, *, resume_uri, save_uri_callback, on_video_uploaded
    ):
        save_uri_callback("fake-resumable-session")
        await on_video_uploaded(f"yt-{session.live_id}", "Replay title")
        return f"yt-{session.live_id}", None

    uploader = AsyncMock(side_effect=upload)
    backend = AsyncMock(return_value=True)
    notification = AsyncMock(return_value=True)
    monkeypatch.setattr(youtube_uploader, "_upload_to_youtube", uploader)
    monkeypatch.setattr(youtube_uploader, "_format_title", lambda meta: "Replay title")
    monkeypatch.setattr(youtube_worker.r2_uploader, "update_youtube_metadata", backend)
    monkeypatch.setattr(
        youtube_worker.notifier, "send_replay_live_notification", notification
    )
    monkeypatch.setattr(
        youtube_worker.shutil,
        "disk_usage",
        lambda path: SimpleNamespace(free=10**12),
    )
    return SimpleNamespace(
        config=config,
        drive=drive,
        uploader=uploader,
        backend=backend,
        notification=notification,
        worker=YouTubeWorker(config, drive),
    )


async def scan_and_drain(worker):
    await worker.scan_once()
    if worker._active:
        await asyncio.gather(*list(worker._active.values()))
    await worker.close()
    assert not worker._active
    assert worker._reserved == 0


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("size", "999", "size"),
        ("md5Checksum", "0" * 32, "checksum"),
    ],
)
def test_archive_safety_log_identifies_file_and_reason(
    harness, caplog, field, value, reason
):
    h = harness
    key = h.drive.add_archive()
    video_id = f"{key}/live1.mp4"
    h.drive.files[video_id][field] = value
    asyncio.run(scan_and_drain(h.worker))
    assert (
        "needs attention (DriveSafetyError): Archive asset 'live1.mp4'" in caplog.text
    )
    assert f"({reason})" in caplog.text
    assert key in caplog.text
    h.uploader.assert_not_awaited()
    assert key in h.drive.archives
    assert not any(call[0] in {"download", "delete"} for call in h.drive.calls)


def test_success_immediately_announces_configured_upload_delay(harness, caplog):
    h = harness
    h.config.youtube_upload_delay_minutes = 60
    h.drive.add_archive()
    caplog.set_level("INFO", logger="gdrive")
    asyncio.run(scan_and_drain(h.worker))
    messages = [record.message for record in caplog.records]
    complete = messages.index("Drive-to-YouTube complete: live1")
    delay_messages = [
        message for message in messages if "YouTube upload delay active" in message
    ]
    assert len(delay_messages) == 1
    assert "1h 0m remaining" in delay_messages[0]
    assert messages.index(delay_messages[0]) > complete


def receipt(key, **changes):
    return {
        "schema_version": 1,
        "archive_key": key,
        "live_id": "live1",
        "member_nickname": "Erine",
        "youtube_id": "existing-video",
        "youtube_title": "Replay title",
        "completed_at": "2026-01-01T00:00:00Z",
        "retention": "keep",
        "retention_reason": "member_exception",
        **changes,
    }


@pytest.mark.parametrize("priority", [{"erine": 0, "oline": 1}, {}])
def test_priority_is_selected_before_any_media_download(harness, priority):
    h = harness
    h.config.youtube_upload_priority_ranks = priority
    other = h.drive.add_archive("other", "Other", 100)
    small = h.drive.add_archive("small", " ErInE ", 10)
    oline = h.drive.add_archive("oline", "Oline", 90)
    large = h.drive.add_archive("large", "Erine", 30)
    h.drive.calls.clear()
    expected = (
        [large, small, oline, other] if priority else [other, oline, large, small]
    )

    async def run():
        for key in expected:
            start = len(h.drive.calls)
            await h.worker.scan_once()
            await asyncio.gather(*list(h.worker._active.values()))
            downloads = [c[1] for c in h.drive.calls[start:] if c[0] == "download"]
            assert downloads == [
                f"{key}/{h.drive.archives[key]['name']}.mp4",
                f"{key}/{h.drive.archives[key]['name']}.json",
            ]
        await h.worker.close()

    asyncio.run(run())
    assert [call.args[0].live_id for call in h.uploader.await_args_list] == [
        h.drive.archives[key]["name"] for key in expected
    ]


@pytest.mark.parametrize(
    "master,enabled", [(True, False), (False, True), (False, False)]
)
def test_disabled_feature_makes_no_calls_or_markers(harness, master, enabled):
    h = harness
    key = h.drive.add_archive()
    h.drive.upsert_json(
        key,
        DONE_NAME,
        receipt(key, retention="delete", retention_reason="deletion_enabled"),
    )
    h.config.backup_to_gdrive = master
    h.config.gdrive_to_youtube = enabled
    h.drive.calls.clear()
    before = copy.deepcopy(h.drive.payloads)
    asyncio.run(scan_and_drain(h.worker))
    assert h.drive.calls == []
    assert h.drive.payloads == before
    assert not h.worker.state_dir.exists()
    assert not h.worker.staging.exists()
    h.uploader.assert_not_awaited()
    h.backend.assert_not_awaited()
    h.notification.assert_not_awaited()


@pytest.mark.parametrize(
    "delete,keep,reason",
    [
        (True, set(), "deletion_enabled"),
        (False, set(), "deletion_disabled"),
        (True, {"erine"}, "member_exception"),
    ],
)
def test_success_commits_receipt_before_delete_or_keep(harness, delete, keep, reason):
    h = harness
    key = h.drive.add_archive(nickname=" ErInE ")
    h.config.gdrive_delete_after_youtube_upload = delete
    h.config.gdrive_keep_members_normalized = keep
    h.drive.calls.clear()
    asyncio.run(scan_and_drain(h.worker))
    h.uploader.assert_awaited_once()
    h.backend.assert_awaited_once()
    h.notification.assert_awaited_once()
    assert ("write", key, DONE_NAME) in h.drive.calls
    if reason == "deletion_enabled":
        assert h.drive.calls.index(("write", key, DONE_NAME)) < h.drive.calls.index(
            ("delete", key, key)
        )
        assert key not in h.drive.archives
    else:
        saved = h.drive.get_json(f"{key}/{DONE_NAME}")
        assert saved["retention"] == "keep"
        assert saved["retention_reason"] == reason
        assert saved["youtube_id"] == "yt-live1"
        assert not any(c[0] == "delete" for c in h.drive.calls)
    history = [
        json.loads(line)
        for line in h.config.uploads_history_path.read_text().splitlines()
    ]
    assert len(history) == 1
    assert history[0]["archive_key"] == key
    assert not (h.worker.staging / key).exists()
    assert not h.worker._job_path(key).exists()


def test_stale_listing_after_cleanup_skips_deleted_archive_and_continues(
    harness, monkeypatch, caplog
):
    h = harness
    deleted = h.drive.add_archive()
    stale = copy.deepcopy(h.drive.archives[deleted])
    h.config.gdrive_delete_after_youtube_upload = True
    asyncio.run(scan_and_drain(h.worker))
    assert deleted not in h.drive.archives
    h.uploader.assert_awaited_once()

    healthy = h.drive.add_archive("healthy")
    healthy_folder = copy.deepcopy(h.drive.archives[healthy])
    monkeypatch.setattr(h.drive, "list_archives", lambda: [stale, healthy_folder])
    ensure = Mock(side_effect=AssertionError("Reader must never ensure an archive"))
    create = Mock(side_effect=AssertionError("Reader must never create a folder"))
    monkeypatch.setattr(h.drive, "ensure_archive", ensure, raising=False)
    monkeypatch.setattr(h.drive, "create", create, raising=False)
    h.uploader.reset_mock()
    h.drive.calls.clear()
    caplog.clear()
    caplog.set_level(logging.INFO, logger="gdrive")

    asyncio.run(scan_and_drain(YouTubeWorker(h.config, h.drive)))

    assert h.drive.calls[0] == ("get", deleted, deleted)
    assert ("get", healthy, healthy) in h.drive.calls
    assert not any(
        call[0] in {"children", "download", "write", "delete"}
        and call[1].startswith(deleted)
        for call in h.drive.calls
    )
    ensure.assert_not_called()
    create.assert_not_called()
    h.uploader.assert_awaited_once()
    assert h.uploader.call_args.args[0].live_id == "healthy"
    assert not h.drive.archives
    assert any(
        record.levelno == logging.INFO
        and "skipping stale listing" in record.getMessage()
        and deleted in record.getMessage()
        for record in caplog.records
    )
    assert not any(record.levelno >= logging.ERROR for record in caplog.records)
    assert "DriveSafetyError" not in caplog.text


def test_archive_lookup_403_is_an_error_not_a_stale_listing(
    harness, monkeypatch, caplog
):
    h = harness
    key = h.drive.add_archive()
    error = HttpError(Response({"status": "403"}), b'{"error":{"message":"Forbidden"}}')
    get_archive = Mock(side_effect=error)
    monkeypatch.setattr(h.drive, "get_archive", get_archive)
    h.drive.calls.clear()
    caplog.set_level(logging.INFO, logger="gdrive")

    asyncio.run(scan_and_drain(h.worker))

    get_archive.assert_called_once_with(key, key)
    assert "needs attention (HttpError)" in caplog.text

    assert any(record.levelno >= logging.ERROR for record in caplog.records)
    assert "skipping stale listing" not in caplog.text
    assert h.drive.calls == [("list",)]
    assert key in h.drive.archives
    h.uploader.assert_not_awaited()


def test_keep_is_nonretroactive_after_member_removed(harness):
    h = harness
    key = h.drive.add_archive()
    h.config.gdrive_delete_after_youtube_upload = True
    h.config.gdrive_keep_members_normalized = {"erine"}
    asyncio.run(scan_and_drain(h.worker))
    original = h.drive.get_json(f"{key}/{DONE_NAME}")
    h.config.gdrive_keep_members_normalized = set()
    h.drive.calls.clear()
    asyncio.run(scan_and_drain(YouTubeWorker(h.config, h.drive)))
    assert h.drive.get_json(f"{key}/{DONE_NAME}") == original
    assert key in h.drive.archives
    assert not any(c[0] in {"download", "delete", "write"} for c in h.drive.calls)
    h.uploader.assert_awaited_once()


def test_quota_saves_cooldown_and_blocks_next_download_even_after_restart(harness):
    h = harness
    first = h.drive.add_archive("first", size=100)
    h.drive.add_archive("second", size=10)
    h.uploader.side_effect = youtube_uploader.QuotaExceededError()
    before = time.time()
    asyncio.run(scan_and_drain(h.worker))
    deadline = float(h.worker.cooldown_path.read_text())
    assert before + 86400 <= deadline <= time.time() + 86400
    assert not (h.worker.staging / first).exists()
    state = read_json(h.worker._job_path(first))
    assert "resume_uri" not in state
    assert "upload_started" not in state
    h.drive.calls.clear()
    asyncio.run(scan_and_drain(YouTubeWorker(h.config, h.drive)))
    assert not any(c[0] in {"download", "delete", "write"} for c in h.drive.calls)
    h.uploader.assert_awaited_once()
    h.backend.assert_not_awaited()
    h.notification.assert_not_awaited()
    assert len(h.drive.archives) == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"shared": True},
        {"ownedByMe": False},
        {"parents": ["unmanaged-root"]},
        {"appProperties": {"archive_key": "not-hex"}},
    ],
)
def test_untrusted_archive_is_rejected_before_reading_children(
    harness, changes, caplog
):
    h = harness
    key = h.drive.add_archive()
    h.drive.archives[key].update(changes)
    h.drive.calls.clear()
    asyncio.run(scan_and_drain(h.worker))
    assert "needs attention" in caplog.text
    assert not any(
        c[0] in {"children", "json", "download", "write", "delete"}
        for c in h.drive.calls
    )
    h.uploader.assert_not_awaited()
    h.backend.assert_not_awaited()
    h.notification.assert_not_awaited()


def test_verified_archive_id_must_match_listing(harness, monkeypatch, caplog):
    h = harness
    key = h.drive.add_archive()
    folder = copy.deepcopy(h.drive.archives[key])
    verified = {**folder, "id": "different-folder"}
    get_archive = Mock(return_value=verified)
    monkeypatch.setattr(h.drive, "get_archive", get_archive)
    h.drive.calls.clear()
    asyncio.run(scan_and_drain(h.worker))
    get_archive.assert_called_once_with(folder["id"], key)
    assert h.drive.calls == [("list",)]
    assert "Archive identity mismatch" in caplog.text
    assert "needs attention" in caplog.text
    h.uploader.assert_not_awaited()
    h.backend.assert_not_awaited()
    h.notification.assert_not_awaited()


@pytest.mark.parametrize("source_kind", ["directory", "dangling_symlink"])
def test_existing_source_defers_consumption_until_removed(harness, source_kind):
    h = harness
    key = h.drive.add_archive()
    source = h.config.recordings_dir / "live1"
    source.parent.mkdir(parents=True)
    if source_kind == "directory":
        source.mkdir()
    else:
        source.symlink_to(source.parent / "missing-recording", target_is_directory=True)
    before = copy.deepcopy(h.drive.payloads)
    h.drive.calls.clear()
    asyncio.run(scan_and_drain(h.worker))
    assert h.drive.payloads == before
    assert not any(c[0] in {"download", "write", "delete"} for c in h.drive.calls)
    assert not h.worker.staging.exists()
    assert not h.worker.state_dir.exists()
    h.uploader.assert_not_awaited()
    h.backend.assert_not_awaited()
    h.notification.assert_not_awaited()
    if source_kind == "directory":
        source.rmdir()
    else:
        source.unlink()
    asyncio.run(scan_and_drain(YouTubeWorker(h.config, h.drive)))
    h.uploader.assert_awaited_once()
    h.backend.assert_awaited_once()
    h.notification.assert_awaited_once()
    assert h.drive.get_json(f"{key}/{DONE_NAME}")["youtube_id"] == "yt-live1"


def test_insufficient_disk_blocks_download(harness, monkeypatch):
    h = harness
    h.drive.add_archive()
    monkeypatch.setattr(
        youtube_worker.shutil,
        "disk_usage",
        lambda path: SimpleNamespace(free=youtube_worker.DISK_MARGIN),
    )
    h.drive.calls.clear()
    asyncio.run(scan_and_drain(h.worker))
    assert not any(c[0] in {"download", "write", "delete"} for c in h.drive.calls)
    h.uploader.assert_not_awaited()
    h.backend.assert_not_awaited()
    h.notification.assert_not_awaited()


def test_backend_retry_uses_checkpoint_without_duplicate_upload(harness):
    h = harness
    key = h.drive.add_archive()
    h.backend.side_effect = [False, True]
    asyncio.run(scan_and_drain(h.worker))
    state = read_json(h.worker._job_path(key))
    assert state["youtube_id"] == "yt-live1"
    assert h.drive.get_json(f"{key}/{MANIFEST_NAME}")["youtube_id"] == "yt-live1"
    assert f"{key}/{DONE_NAME}" not in h.drive.files
    h.notification.assert_not_awaited()
    h.drive.calls.clear()
    asyncio.run(scan_and_drain(YouTubeWorker(h.config, h.drive)))
    h.uploader.assert_awaited_once()
    assert h.backend.await_count == 2
    assert h.backend.await_args_list[0].args[1] == h.backend.await_args_list[1].args[1]
    h.notification.assert_awaited_once()
    assert not any(c == ("download", f"{key}/live1.mp4") for c in h.drive.calls)
    assert h.drive.get_json(f"{key}/{DONE_NAME}")["youtube_id"] == "yt-live1"


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"archive_key": "wrong"},
        {"youtube_id": ""},
        {"retention": None},
        {"retention": "trash"},
        {"retention_reason": "unknown"},
        {"retention": "delete", "retention_reason": "member_exception"},
        {"retention": "keep", "retention_reason": "deletion_enabled"},
    ],
)
def test_malformed_receipts_prevent_upload_and_delete(harness, changes, caplog):
    h = harness
    key = h.drive.add_archive()
    h.config.gdrive_delete_after_youtube_upload = True
    h.drive.upsert_json(key, DONE_NAME, receipt(key, **changes))
    h.drive.calls.clear()
    asyncio.run(scan_and_drain(h.worker))
    assert key in h.drive.archives
    assert "needs attention" in caplog.text
    assert not any(c[0] in {"download", "write", "delete"} for c in h.drive.calls)
    h.uploader.assert_not_awaited()
    h.backend.assert_not_awaited()
    h.notification.assert_not_awaited()


def test_completed_receipt_skips_upload_without_ready_marker(harness):
    h = harness
    key = h.drive.add_archive()
    h.drive.upsert_json(key, DONE_NAME, receipt(key))
    del h.drive.files[f"{key}/{READY_NAME}"]
    h.drive.calls.clear()
    asyncio.run(scan_and_drain(h.worker))
    assert not any(c[0] in {"download", "write", "delete"} for c in h.drive.calls)
    h.uploader.assert_not_awaited()
    h.backend.assert_not_awaited()
    h.notification.assert_not_awaited()


@pytest.mark.parametrize("limit", [1, 2])
def test_concurrency_slots_cover_download_upload_and_finalization(harness, limit):
    h = harness
    h.config.max_concurrent_uploads = limit
    for index in range(4):
        h.drive.add_archive(f"live{index}")
    h.drive.calls.clear()

    async def run():
        entered = asyncio.Event()
        release = asyncio.Event()
        count = 0

        async def backend(*args):
            nonlocal count
            count += 1
            if count == limit:
                entered.set()
            await release.wait()
            return True

        h.backend.side_effect = backend
        try:
            await h.worker.scan_once()
            await asyncio.wait_for(entered.wait(), timeout=5)
            assert len(h.worker._active) == limit
            assert h.uploader.await_count == limit
            downloads = [c for c in h.drive.calls if c[0] == "download"]
            assert len({c[1].split("/")[0] for c in downloads}) == limit
            await h.worker.scan_once()
            assert [c for c in h.drive.calls if c[0] == "download"] == downloads
            assert h.uploader.await_count == limit
        finally:
            release.set()
            await h.worker.close()
        assert not h.worker._active
        assert h.worker._reserved == 0

    asyncio.run(run())


@pytest.mark.parametrize(
    "failure",
    ["backend_false", "backend_network", "upload_network", "download_network"],
)
def test_failed_jobs_remove_staging_but_preserve_drive_and_journal(
    harness, monkeypatch, failure
):
    h = harness
    key = h.drive.add_archive()
    if failure == "backend_false":
        h.backend.return_value = False
    elif failure == "backend_network":
        h.backend.side_effect = ConnectionError("offline")
    elif failure == "upload_network":

        async def interrupted(session, config, **kwargs):
            kwargs["save_uri_callback"]("recoverable-session")
            raise ConnectionError("offline")

        h.uploader.side_effect = interrupted
    else:
        download = h.drive.download_file

        def interrupted_download(file_id, destination, **kwargs):
            download(file_id, destination, **kwargs)
            raise ConnectionError("offline")

        monkeypatch.setattr(h.drive, "download_file", interrupted_download)
    asyncio.run(scan_and_drain(h.worker))
    assert not (h.worker.staging / key).exists()
    assert key in h.drive.archives
    assert f"{key}/{DONE_NAME}" not in h.drive.files
    assert f"{key}/live1.mp4" in h.drive.files
    h.notification.assert_not_awaited()
    if failure.startswith("backend"):
        assert read_json(h.worker._job_path(key))["youtube_id"] == "yt-live1"
    elif failure == "upload_network":
        assert read_json(h.worker._job_path(key))["resume_uri"] == "recoverable-session"


def test_checkpoint_removes_video_after_local_id_before_remote_write(
    harness, monkeypatch
):
    h = harness
    key = h.drive.add_archive()
    upsert = h.drive.upsert_json
    checked = []

    def fail_manifest_write(parent, name, value):
        if name == MANIFEST_NAME:
            assert read_json(h.worker._job_path(key))["youtube_id"] == "yt-live1"
            local = h.worker.staging / key
            assert not (local / "live1.mp4").exists()
            assert (local / "live1.json").exists()
            checked.append(True)
            raise ConnectionError("remote checkpoint unavailable")
        return upsert(parent, name, value)

    monkeypatch.setattr(h.drive, "upsert_json", fail_manifest_write)
    asyncio.run(scan_and_drain(h.worker))
    assert checked == [True]
    assert not (h.worker.staging / key).exists()
    assert read_json(h.worker._job_path(key))["youtube_id"] == "yt-live1"
    h.backend.assert_not_awaited()
    h.notification.assert_not_awaited()


def test_restart_clears_stale_managed_staging_once_without_losing_journal(harness):
    h = harness
    key = hashlib.sha256(b"stale-job").hexdigest()
    stale = h.worker.staging / key
    stale.mkdir(parents=True)
    (stale / "old.mp4").write_bytes(b"stale media")
    unmanaged = h.worker.staging / "manual-files"
    unmanaged.mkdir()
    (unmanaged / "keep.txt").write_text("not managed")
    state = {"youtube_id": "saved-id", "resume_uri": "saved-session"}
    write_json(h.worker._job_path(key), state)

    async def run():
        worker = YouTubeWorker(h.config, h.drive)
        await worker.scan_once()
        assert not stale.exists()
        assert read_json(worker._job_path(key)) == state
        assert (unmanaged / "keep.txt").read_text() == "not managed"
        # A subsequent scan must not repeat startup sweeping of managed names.
        stale.mkdir()
        (stale / "active.mp4").write_bytes(b"current media")
        await worker.scan_once()
        assert (stale / "active.mp4").exists()
        await worker.close()
        await scan_and_drain(YouTubeWorker(h.config, h.drive))
        assert not stale.exists()
        assert read_json(worker._job_path(key)) == state

    asyncio.run(run())
    h.uploader.assert_not_awaited()


def test_stop_event_set_during_scan_prevents_admission(harness, monkeypatch):
    h = harness
    h.drive.add_archive()
    stop = asyncio.Event()
    h.worker.stop_event = stop
    original = h.drive.list_archives

    def stop_while_listing():
        result = original()
        stop.set()
        return result

    monkeypatch.setattr(h.drive, "list_archives", stop_while_listing)
    h.drive.calls.clear()
    asyncio.run(scan_and_drain(h.worker))
    assert stop.is_set()
    assert not any(c[0] in {"download", "write", "delete"} for c in h.drive.calls)
    assert not h.worker.staging.exists()
    assert not h.worker.state_dir.exists()
    h.uploader.assert_not_awaited()
    h.backend.assert_not_awaited()
    h.notification.assert_not_awaited()


@pytest.mark.parametrize("control", ["quota", "completion_delay"])
def test_persisted_cooldown_blocks_new_downloads_until_expiry(
    harness, monkeypatch, control
):
    h = harness
    h.drive.add_archive()
    now = [2_000_000_000.0]
    monkeypatch.setattr(youtube_worker.time, "time", lambda: now[0])
    deadline = now[0] + 3600
    if control == "quota":
        h.worker.cooldown_path.parent.mkdir(parents=True)
        h.worker.cooldown_path.write_text(str(deadline))
    else:
        h.worker.timing_path.parent.mkdir(parents=True)
        h.worker.timing_path.write_text(str(deadline))
    h.drive.calls.clear()

    async def run():
        await h.worker.scan_once()
        await h.worker.scan_once()
        assert not h.worker._active
        assert not any(c[0] == "download" for c in h.drive.calls)
        h.uploader.assert_not_awaited()
        now[0] = deadline + 1
        await scan_and_drain(h.worker)

    asyncio.run(run())
    h.uploader.assert_awaited_once()


def test_discovered_completion_recovers_history_and_fixed_deadline(
    harness, monkeypatch
):
    h = harness
    completed = 2_000_000_000.0
    now = [completed + 60]
    monkeypatch.setattr(youtube_worker.time, "time", lambda: now[0])
    h.config.youtube_upload_delay_minutes = 30
    key = h.drive.add_archive()
    h.drive.add_archive("pending")
    saved = receipt(
        key, completed_at=datetime.fromtimestamp(completed, timezone.utc).isoformat()
    )
    h.drive.upsert_json(key, DONE_NAME, saved)
    h.drive.calls.clear()
    deadline = completed + 1800

    async def run():
        for offset in [60, 600, 1200]:
            now[0] = completed + offset
            await scan_and_drain(YouTubeWorker(h.config, h.drive))
            assert float(h.worker.timing_path.read_text()) == deadline
            history = [
                json.loads(line)
                for line in h.config.uploads_history_path.read_text().splitlines()
            ]
            assert len(history) == 1
            assert history[0]["archive_key"] == key
            assert history[0]["uploaded_at"] == saved["completed_at"]
            assert not any(c[0] == "download" for c in h.drive.calls)
            h.uploader.assert_not_awaited()
        now[0] = deadline + 1
        await scan_and_drain(YouTubeWorker(h.config, h.drive))

    asyncio.run(run())
    h.uploader.assert_awaited_once()
    assert h.uploader.await_args.args[0].live_id == "pending"
    assert h.drive.get_json(f"{key}/{DONE_NAME}") == saved


@pytest.mark.parametrize(
    "field,invalid",
    [
        ("member_nickname", "missing"),
        ("member_nickname", None),
        ("member_nickname", 123),
        ("completed_at", "missing"),
        ("completed_at", None),
        ("completed_at", 123),
        ("completed_at", "invalid_time"),
        ("completed_at", "naive_time"),
    ],
)
def test_incomplete_receipt_fails_closed_before_completion_or_deletion(
    harness, caplog, field, invalid
):
    h = harness
    key = h.drive.add_archive()
    h.config.gdrive_delete_after_youtube_upload = True
    saved = receipt(key, retention="delete", retention_reason="deletion_enabled")
    if invalid == "missing":
        del saved[field]
    elif invalid == "naive_time":
        saved[field] = "2026-01-01T00:00:00"
    else:
        saved[field] = invalid
    h.drive.upsert_json(key, DONE_NAME, saved)
    h.drive.calls.clear()
    asyncio.run(scan_and_drain(h.worker))
    assert "needs attention" in caplog.text
    assert key in h.drive.archives
    assert not any(c[0] in {"download", "write", "delete"} for c in h.drive.calls)
    assert not h.worker.timing_path.exists()
    assert not h.config.uploads_history_path.exists()
    h.uploader.assert_not_awaited()
    h.backend.assert_not_awaited()
    h.notification.assert_not_awaited()
