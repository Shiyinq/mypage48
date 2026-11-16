"""Offline controller lifecycle and ownership contracts."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from recorder.src.gdrive import service
from recorder.src.gdrive.backup_worker import BackupWorker
from recorder.src.gdrive.youtube_worker import YouTubeWorker
from recorder.src.process_lock import process_lock


@pytest.fixture
def harness(tmp_path, monkeypatch):
    config = SimpleNamespace(
        logs_dir=tmp_path,
        backup_to_gdrive=True,
        gdrive_to_youtube=True,
        max_concurrent_uploads=1,
        google_client_id="client",
        google_client_secret="secret",
        gdrive_refresh_token="token",
        poll_interval=15,
    )
    client = Mock()
    factory = Mock(return_value=client)
    backup = SimpleNamespace(scan_once=AsyncMock())
    replay = SimpleNamespace(scan_once=AsyncMock(), close=AsyncMock())
    monkeypatch.setattr(service.DriveClient, "from_config", factory)
    monkeypatch.setattr(service, "BackupWorker", Mock(return_value=backup))
    monkeypatch.setattr(service, "YouTubeWorker", Mock(return_value=replay))
    return SimpleNamespace(
        config=config, client=client, factory=factory, backup=backup, replay=replay
    )


def test_disabled_master_stays_alive_without_credentials_or_drive(harness):
    h = harness
    h.config.backup_to_gdrive = False
    h.config.google_client_id = h.config.google_client_secret = ""
    h.config.gdrive_refresh_token = ""
    h.config.max_concurrent_uploads = 0

    async def run():
        stop = asyncio.Event()
        task = asyncio.create_task(service.GDriveService(h.config).run(stop))
        try:
            await asyncio.sleep(0)
            assert not task.done()
            h.factory.assert_not_called()
            service.BackupWorker.assert_not_called()
            service.YouTubeWorker.assert_not_called()
        finally:
            stop.set()
            await asyncio.wait_for(task, 2)

    asyncio.run(run())
    h.client.ensure_root.assert_not_called()


@pytest.mark.parametrize(
    "missing", ["google_client_id", "google_client_secret", "gdrive_refresh_token"]
)
def test_enabled_missing_credentials_errors_before_api(harness, missing):
    setattr(harness.config, missing, "")
    with pytest.raises(ValueError, match="OAuth credentials are missing"):
        asyncio.run(service.GDriveService(harness.config).run(asyncio.Event()))
    harness.factory.assert_not_called()
    harness.client.ensure_root.assert_not_called()


@pytest.mark.parametrize("youtube_enabled", [False, True])
def test_worker_selection_and_graceful_stop(harness, youtube_enabled):
    h = harness
    h.config.gdrive_to_youtube = youtube_enabled

    async def run():
        stop = asyncio.Event()
        release = asyncio.Event()
        backup_entered = asyncio.Event()
        replay_entered = asyncio.Event()
        finished = []

        async def scan(label, entered):
            entered.set()
            await release.wait()
            finished.append(label)

        async def backup_scan():
            await scan("backup", backup_entered)

        async def replay_scan():
            await scan("youtube", replay_entered)

        h.backup.scan_once.side_effect = backup_scan
        h.replay.scan_once.side_effect = replay_scan
        task = asyncio.create_task(service.GDriveService(h.config).run(stop))
        try:
            await asyncio.wait_for(backup_entered.wait(), 2)
            if youtube_enabled:
                await asyncio.wait_for(replay_entered.wait(), 2)
            else:
                h.replay.scan_once.assert_not_awaited()
            stop.set()
            await asyncio.sleep(0)
            assert not task.done(), "Shutdown must drain in-flight scans"
            h.replay.close.assert_not_awaited()
        finally:
            stop.set()
            release.set()
            await asyncio.wait_for(task, 2)
        assert h.backup.stop_event is stop
        assert h.replay.stop_event is stop
        assert sorted(finished) == (
            ["backup", "youtube"] if youtube_enabled else ["backup"]
        )
        h.replay.close.assert_awaited_once()
        h.backup.scan_once.assert_awaited_once()
        assert h.replay.scan_once.await_count == int(youtube_enabled)

    asyncio.run(run())
    h.factory.assert_called_once_with(h.config)
    h.client.ensure_root.assert_called_once_with()


def test_upload_and_gdrive_locks_coexist_and_reject_duplicates(tmp_path):
    with process_lock(tmp_path, "upload"), process_lock(tmp_path, "gdrive"):
        for role in ("upload", "gdrive"):
            with pytest.raises(RuntimeError, match=f"Another {role} controller"):
                with process_lock(tmp_path, role):
                    pytest.fail("Duplicate controller acquired ownership")
    for role in ("upload", "gdrive"):
        with process_lock(tmp_path, role):
            pass


def test_service_stop_propagates_to_real_workers_and_blocks_new_admission(
    harness, tmp_path, monkeypatch
):
    h = harness
    h.config.recordings_dir = tmp_path / "recordings"
    h.config.recordings_dir.mkdir()
    folder = h.config.recordings_dir / "pending"
    folder.mkdir()
    (folder / ".r2_done").touch()
    backup = BackupWorker(h.config, h.client)
    replay = YouTubeWorker(h.config, h.client)
    backup_job = Mock()
    replay_job = AsyncMock()
    monkeypatch.setattr(backup, "_backup", backup_job)
    monkeypatch.setattr(replay, "_process", replay_job)
    monkeypatch.setattr(service, "BackupWorker", Mock(return_value=backup))
    monkeypatch.setattr(service, "YouTubeWorker", Mock(return_value=replay))
    manifest = {
        "archive_key": "a" * 64,
        "live_id": "pending",
        "files": [{"role": "video", "size": 5}],
    }
    h.client.list_archives.return_value = [
        {"id": "archive", "appProperties": {"archive_key": manifest["archive_key"]}}
    ]
    load = AsyncMock(return_value=manifest)
    monkeypatch.setattr(replay, "_load", load)
    backup_scan = backup.scan_once
    replay_scan = replay.scan_once

    async def run():
        stop = asyncio.Event()
        release = asyncio.Event()
        backup_entered = asyncio.Event()
        replay_entered = asyncio.Event()

        async def gated_backup():
            backup_entered.set()
            await release.wait()
            await backup_scan()

        async def gated_replay():
            replay_entered.set()
            await release.wait()
            await replay_scan()

        monkeypatch.setattr(backup, "scan_once", gated_backup)
        monkeypatch.setattr(replay, "scan_once", gated_replay)
        task = asyncio.create_task(service.GDriveService(h.config).run(stop))
        try:
            await asyncio.wait_for(backup_entered.wait(), 2)
            await asyncio.wait_for(replay_entered.wait(), 2)
            assert backup.stop_event is stop
            assert replay.stop_event is stop
            stop.set()
            assert replay._blocked()
            assert not task.done()
        finally:
            stop.set()
            release.set()
            await asyncio.wait_for(task, 2)
        backup_job.assert_not_called()
        replay_job.assert_not_awaited()
        load.assert_awaited_once()
        assert not replay._active
        assert replay._reserved == 0
        assert replay._stopping
        assert not replay.staging.exists()
        assert folder.exists()
        with process_lock(h.config.logs_dir, "gdrive"):
            pass

    asyncio.run(run())
