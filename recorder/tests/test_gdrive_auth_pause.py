"""Offline contracts for a client-wide, restart-only Drive authorization pause."""

import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from google.auth.exceptions import RefreshError, TransportError
from googleapiclient.errors import HttpError
from httplib2 import Response

from recorder.src.gdrive import client as drive_module
from recorder.src.gdrive.client import DriveClient

PAUSE_MESSAGE = (
    "Google Drive authorization invalid; all Drive processing paused until "
    "credentials are replaced and the GDrive service is restarted"
)
TIMEOUT = 5


def authorization_error():
    # Resolve at test runtime so an unimplemented API fails tests, not collection.
    error = drive_module.DriveAuthorizationError
    assert issubclass(error, RuntimeError)
    return error


def critical_records(caplog):
    return [record for record in caplog.records if record.levelno == logging.CRITICAL]


def failing_client(error):
    service = MagicMock()
    service.files.return_value.get.return_value.execute.side_effect = error
    return DriveClient(service), service


@pytest.mark.parametrize(
    "code",
    [
        "invalid_grant",
        "invalid_client",
        "unauthorized_client",
        "invalid_scope",
        "invalid_token",
    ],
)
def test_permanent_refresh_error_latches_real_decorator_once(code, caplog):
    error_type = authorization_error()
    client, service = failing_client(RefreshError(f"{code}: credentials rejected"))
    assert client.authorization_failed is False
    assert client.raise_if_authorization_failed() is None

    for _ in range(3):
        with pytest.raises(error_type):
            client.get_file("asset")
        assert client.authorization_failed is True
        with pytest.raises(error_type):
            client.raise_if_authorization_failed()

    # The latch guards other decorated entry points, not just the failed method.
    with pytest.raises(error_type):
        client.list_children("archive")
    service.files.assert_called_once_with()
    service.files.return_value.get.return_value.execute.assert_called_once_with(
        num_retries=3
    )
    records = critical_records(caplog)
    assert len(records) == 1
    assert records[0].getMessage() == PAUSE_MESSAGE

    # Replacing a transport's response cannot unpause an existing client.
    service.files.return_value.get.return_value.execute.side_effect = None
    with pytest.raises(error_type):
        client.get_file("asset")
    fresh = DriveClient(service)
    assert fresh.authorization_failed is False
    assert fresh.raise_if_authorization_failed() is None
    fresh.get_file("asset")
    assert len(critical_records(caplog)) == 1
    assert critical_records(caplog)[0].getMessage() == PAUSE_MESSAGE


@pytest.mark.parametrize(
    "error",
    [
        RefreshError("temporarily_unavailable: try again"),
        RefreshError("server_error: token endpoint unavailable"),
        RefreshError("token endpoint returned HTTP 503", retryable=True),
        RefreshError("connection timed out"),
        RefreshError("invalid_grant: retryable endpoint failure", retryable=True),
        TransportError("invalid_grant: transport failed, not an OAuth rejection"),
        TimeoutError("token request timed out"),
        RuntimeError("invalid_grant: not a Google RefreshError"),
    ],
    ids=[
        "temporary",
        "server",
        "retryable",
        "timeout-refresh",
        "retryable-invalid-grant",
        "transport",
        "timeout",
        "runtime",
    ],
)
def test_transient_and_non_refresh_errors_do_not_pause(error, caplog):
    client, service = failing_client(error)
    for _ in range(2):
        with pytest.raises(type(error)) as caught:
            client.get_file("asset")
        assert caught.value is error
        assert client.authorization_failed is False
        assert client.raise_if_authorization_failed() is None
    assert service.files.return_value.get.return_value.execute.call_count == 2
    assert not critical_records(caplog)


@pytest.mark.parametrize("status", [401, 403])
def test_http_authorization_vs_permission_failure(status, caplog):
    error = HttpError(
        Response({"status": str(status)}),
        b'{"error": {"message": "Request rejected"}}',
    )
    client, service = failing_client(error)
    for attempt in range(3):
        expected = authorization_error() if status == 401 else HttpError
        with pytest.raises(expected) as caught:
            client.get_file("asset")
        assert client.authorization_failed is (status == 401)
        if status == 403:
            assert caught.value is error
            assert client.raise_if_authorization_failed() is None
        elif attempt == 0:
            assert caught.value.__cause__ is error
    assert service.files.return_value.get.return_value.execute.call_count == (
        1 if status == 401 else 3
    )
    records = critical_records(caplog)
    assert len(records) == (1 if status == 401 else 0)
    if records:
        assert records[0].getMessage() == PAUSE_MESSAGE


@pytest.mark.parametrize(
    "code",
    [
        "invalid_grant",
        "invalid_client",
        "unauthorized_client",
        "invalid_scope",
        "invalid_token",
    ],
)
def test_structured_refresh_error_args_latch(code, caplog):
    error = RefreshError(
        "OAuth refresh rejected", {"error": code, "error_description": "Rejected"}
    )
    client, service = failing_client(error)
    for _ in range(2):
        with pytest.raises(authorization_error()):
            client.get_file("asset")
    assert client.authorization_failed is True
    service.files.return_value.get.return_value.execute.assert_called_once_with(
        num_retries=3
    )
    assert [record.getMessage() for record in critical_records(caplog)] == [
        PAUSE_MESSAGE
    ]


@pytest.mark.parametrize("operation", ["write", "download", "get_json"])
def test_chunk_loops_check_shared_pause_before_next_chunk(
    operation, tmp_path, monkeypatch, caplog
):
    service = MagicMock()
    client = DriveClient(service)
    service.files.return_value.get.return_value.execute.return_value = {
        "id": "asset",
        "name": "video.mp4",
        "size": "10",
    }
    destination = tmp_path / "video.mp4"
    destination.write_bytes(b"existing destination")

    def first_chunk(**kwargs):
        client._pause_authorization()
        return None, None if operation == "write" else False

    def guarded_chunk(**kwargs):
        assert (
            next_chunk.call_count == 1
        ), "Paused transfer requested a second API chunk"
        return first_chunk(**kwargs)

    next_chunk = Mock(side_effect=guarded_chunk)
    if operation == "write":
        service.files.return_value.create.return_value.next_chunk = next_chunk
    else:

        def downloader(stream, request, **kwargs):
            return SimpleNamespace(next_chunk=next_chunk)

        monkeypatch.setattr(drive_module, "MediaIoBaseDownload", downloader)

    with pytest.raises(authorization_error()):
        if operation == "write":
            client._write("archive", "video.mp4", Mock(), {})
        elif operation == "download":
            client.download_file("asset", destination)
        else:
            client.get_json("asset")
    next_chunk.assert_called_once_with(num_retries=3)
    assert client.authorization_failed is True
    assert destination.read_bytes() == b"existing destination"
    assert list(tmp_path.iterdir()) == [destination]
    assert [record.getMessage() for record in critical_records(caplog)] == [
        PAUSE_MESSAGE
    ]


@pytest.mark.parametrize("mode", ["already-paused", "scan-raises"])
def test_runtime_controller_loop_waits_without_rescanning(config, mode, caplog):
    from recorder.src.gdrive.service import GDriveService

    client = DriveClient(MagicMock())
    controller = GDriveService(config)
    controller._client = client

    async def run():
        waiting = asyncio.Event()

        class ObservedStop(asyncio.Event):
            async def wait(self):
                waiting.set()
                return await super().wait()

        stop = ObservedStop()

        async def fail():
            client._pause_authorization()
            client.raise_if_authorization_failed()

        scan = AsyncMock(side_effect=fail)
        if mode == "already-paused":
            client._pause_authorization()
        task = asyncio.create_task(controller._loop("backup", scan, stop))
        try:
            await asyncio.wait_for(waiting.wait(), TIMEOUT)
            assert not task.done()
            assert not stop.is_set()
            # Changing credentials in memory must not make a paused loop retry.
            config.gdrive_refresh_token = "replacement"
            await asyncio.sleep(0)
            assert scan.await_count == int(mode == "scan-raises")
        finally:
            stop.set()
            await asyncio.wait_for(task, TIMEOUT)
        assert scan.await_count == int(mode == "scan-raises")

    asyncio.run(run())
    assert [record.getMessage() for record in critical_records(caplog)] == [
        PAUSE_MESSAGE
    ]
    assert not [record for record in caplog.records if record.levelno == logging.ERROR]


def test_parallel_backup_drains_admitted_job_but_admits_no_more(config, monkeypatch):
    from recorder.src.gdrive.backup_worker import BackupWorker

    config.gdrive_max_concurrent_uploads = 2
    client = DriveClient(MagicMock())
    worker = BackupWorker(config, client)
    for name in ("first", "second", "third", "fourth"):
        folder = config.recordings_dir / name
        folder.mkdir()
        (folder / ".r2_done").touch()
    entered = threading.Barrier(2)
    paused = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    def backup(folder):
        entered.wait(timeout=TIMEOUT)
        if folder.name == "first":
            client._pause_authorization()
            paused.set()
            client.raise_if_authorization_failed()
        assert release.wait(timeout=TIMEOUT)
        finished.set()

    job = Mock(side_effect=backup)
    monkeypatch.setattr(worker, "_backup", job)

    async def run():
        task = asyncio.create_task(worker.scan_once())
        try:
            assert await asyncio.to_thread(paused.wait, TIMEOUT)
            await asyncio.sleep(0)
            assert not task.done(), "Already admitted work must be drained"
            assert not finished.is_set()
        finally:
            release.set()
            await asyncio.wait_for(task, TIMEOUT * 2)
        assert finished.is_set()
        await worker.scan_once()

    asyncio.run(run())
    assert sorted(call.args[0].name for call in job.call_args_list) == [
        "first",
        "fourth",
    ]
    assert len(list(config.recordings_dir.iterdir())) == 4


def test_thread_local_transports_share_latch_and_log_once(caplog):
    error_type = authorization_error()
    barrier = threading.Barrier(4)
    services = []
    lock = threading.Lock()

    def factory():
        service = MagicMock()

        def fail(**kwargs):
            barrier.wait(timeout=TIMEOUT)
            raise RefreshError("invalid_grant: revoked")

        service.files.return_value.get.return_value.execute.side_effect = fail
        with lock:
            services.append(service)
        return service

    client = DriveClient(service_factory=factory)

    def attempt():
        with pytest.raises(error_type):
            client.get_file("asset")
        assert client.authorization_failed is True
        with pytest.raises(error_type):
            client.raise_if_authorization_failed()

    # Already admitted requests may fail together; only the log/latch is shared.
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(attempt) for _ in range(4)]
        for future in futures:
            future.result(timeout=TIMEOUT * 2)
    assert len(services) == 4
    assert len(critical_records(caplog)) == 1
    assert critical_records(caplog)[0].getMessage() == PAUSE_MESSAGE
    with pytest.raises(error_type):
        client.get_file("after-failure")
    assert len(services) == 4, "Paused calls must not initialize another transport"
    assert (
        sum(
            item.files.return_value.get.return_value.execute.call_count
            for item in services
        )
        == 4
    )


@pytest.fixture
def config(tmp_path):
    recordings = tmp_path / "recordings"
    recordings.mkdir()
    return SimpleNamespace(
        logs_dir=tmp_path / "logs",
        recordings_dir=recordings,
        backup_to_gdrive=True,
        gdrive_to_youtube=True,
        gdrive_max_concurrent_uploads=1,
        max_concurrent_uploads=1,
        google_client_id="client",
        google_client_secret="secret",
        gdrive_refresh_token="drive-token",
        youtube_refresh_token="youtube-token",
        poll_interval=15,
    )


@pytest.mark.parametrize("failure_at", ["from_config", "ensure_root"])
def test_startup_authorization_failure_waits_for_stop(config, monkeypatch, failure_at):
    from recorder.src.gdrive import service

    error = authorization_error()("Drive authorization invalid")
    client = Mock(authorization_failed=True)
    factory = Mock(return_value=client)
    if failure_at == "from_config":
        factory.side_effect = error
    else:
        client.ensure_root.side_effect = error
    monkeypatch.setattr(service.DriveClient, "from_config", factory)
    backup = Mock()
    replay = Mock()
    monkeypatch.setattr(service, "BackupWorker", backup)
    monkeypatch.setattr(service, "YouTubeWorker", replay)

    async def run():
        class ObservedStop(asyncio.Event):
            def __init__(self):
                super().__init__()
                self.waiting = asyncio.Event()

            async def wait(self):
                self.waiting.set()
                return await super().wait()

        stop = ObservedStop()
        task = asyncio.create_task(service.GDriveService(config).run(stop))
        try:
            await asyncio.wait_for(stop.waiting.wait(), 2)
            assert (
                not task.done()
            ), "An invalid token must idle, not crash the controller"
            assert not stop.is_set()
            backup.assert_not_called()
            replay.assert_not_called()
        finally:
            stop.set()
            await asyncio.wait_for(task, 2)

    asyncio.run(run())
    factory.assert_called_once_with(config)
    assert client.ensure_root.call_count == int(failure_at == "ensure_root")


def test_backup_admits_no_jobs_when_already_paused(config, monkeypatch):
    from recorder.src.gdrive.backup_worker import BackupWorker

    folder = config.recordings_dir / "pending"
    folder.mkdir()
    (folder / ".r2_done").touch()
    client = SimpleNamespace(authorization_failed=True)
    worker = BackupWorker(config, client)
    backup = Mock()
    monkeypatch.setattr(worker, "_backup", backup)
    asyncio.run(worker.scan_once())
    backup.assert_not_called()
    assert folder.exists()


def test_backup_stops_admissions_after_first_authorization_failure(config, monkeypatch):
    from recorder.src.gdrive.backup_worker import BackupWorker

    error_type = authorization_error()
    client = SimpleNamespace(authorization_failed=False)
    worker = BackupWorker(config, client)
    for name in ("first", "second", "third"):
        folder = config.recordings_dir / name
        folder.mkdir()
        (folder / ".r2_done").touch()

    def fail(folder):
        client.authorization_failed = True
        raise error_type("Drive authorization invalid")

    backup = Mock(side_effect=fail)
    monkeypatch.setattr(worker, "_backup", backup)

    async def run():
        await worker.scan_once()
        await worker.scan_once()

    asyncio.run(run())
    backup.assert_called_once_with(config.recordings_dir / "first")
    assert len(list(config.recordings_dir.iterdir())) == 3


def test_youtube_authorization_pause_blocks_new_jobs(config, monkeypatch):
    from recorder.src.gdrive.youtube_worker import YouTubeWorker

    client = Mock(authorization_failed=True)
    key = "a" * 64
    client.list_archives.return_value = [
        {"id": "archive", "appProperties": {"archive_key": key}}
    ]
    worker = YouTubeWorker(config, client)
    process = AsyncMock()
    load = AsyncMock(
        return_value={
            "archive_key": key,
            "live_id": "pending",
            "files": [{"role": "video", "size": 5}],
        }
    )
    monkeypatch.setattr(worker, "_load", load)
    monkeypatch.setattr(worker, "_process", process)

    async def run():
        try:
            assert worker._blocked() is True
            await worker.scan_once()
            process.assert_not_awaited()
            assert not worker._active
            assert worker._reserved == 0
        finally:
            await worker.close()

    asyncio.run(run())
