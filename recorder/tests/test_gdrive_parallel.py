"""Offline concurrency regressions for the real DriveClient transfer path."""

import asyncio
import copy
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from googleapiclient.http import MediaFileUpload

from recorder.src.gdrive import client as drive_module
from recorder.src.gdrive.archive import MANIFEST_NAME, READY_NAME, validate_manifest
from recorder.src.gdrive.backup_worker import BackupWorker
from recorder.src.gdrive.client import (
    APP_PROPERTIES,
    FOLDER_MIME,
    DriveClient,
    DriveSafetyError,
)
from recorder.src.gdrive.youtube_worker import YouTubeWorker


TIMEOUT = 10


class Request:
    def __init__(self, service, callback):
        self.service = service
        self.callback = callback

    def execute(self, **kwargs):
        self.service.check_owner()
        return self.callback()

    def next_chunk(self, **kwargs):
        self.service.check_owner()
        assert kwargs == {"num_retries": 3}
        return None, self.callback()


class Service:
    """A Resource/transport stand-in that must never cross thread boundaries."""

    def __init__(self, state, credentials):
        self.state = state
        self.credentials = credentials
        self.owner = threading.get_ident()
        self.transport = object()
        self.uploads = {}
        self.permission_resource = False

    def check_owner(self):
        assert threading.get_ident() == self.owner
        assert self.credentials.owner == self.owner

    def files(self):
        self.check_owner()
        self.permission_resource = False
        return self

    def permissions(self):
        self.check_owner()
        self.permission_resource = True
        return self

    def list(self, **kwargs):
        self.check_owner()
        if self.permission_resource:
            assert kwargs["fileId"] == "managed-root"
            return Request(
                self, lambda: {"permissions": [{"role": "owner", "type": "user"}]}
            )

        def discover():
            self.check_owner()
            with self.state.lock:
                self.state.discoveries += 1
                return {"files": copy.deepcopy(self.state.roots)}

        assert "appProperties" in kwargs["q"]
        return Request(self, discover)

    def create(self, *, body, fields, media_body=None):
        self.check_owner()
        if media_body is None:
            assert body == {
                "name": "JKT48Live",
                "mimeType": FOLDER_MIME,
                "parents": ["root"],
                "appProperties": APP_PROPERTIES,
            }

            def create_root():
                self.check_owner()
                with self.state.lock:
                    self.state.creates += 1
                    root = dict(
                        body,
                        id="managed-root",
                        parents=["my-drive"],
                        shared=False,
                        ownedByMe=True,
                    )
                    self.state.roots.append(root)
                    return copy.deepcopy(root)

            return Request(self, create_root)

        assert isinstance(media_body, MediaFileUpload)
        assert media_body.resumable()
        assert body["parents"] == ["archive"]
        payload = media_body.getbytes(0, media_body.size())
        file_id = body["name"]
        self.uploads[file_id] = {
            **copy.deepcopy(body),
            "id": file_id,
            "size": str(len(payload)),
            "md5Checksum": hashlib.md5(payload).hexdigest(),
            "sha256Checksum": hashlib.sha256(payload).hexdigest(),
        }

        def transfer():
            self.check_owner()
            with self.state.lock:
                self.state.active += 1
                self.state.peak = max(self.state.peak, self.state.active)
                self.state.transfers.append(self)
            try:
                self.state.transfer_gate()
                return {"id": file_id}
            finally:
                with self.state.lock:
                    self.state.active -= 1

        return Request(self, transfer)

    def get(self, *, fileId, fields):
        self.check_owner()

        def fetch():
            self.check_owner()
            if fileId == "root":
                return {"id": "my-drive"}
            if fileId == "managed-root":
                with self.state.lock:
                    return copy.deepcopy(self.state.roots[0])
            if fileId == "metadata":
                return {"id": "metadata"}
            return copy.deepcopy(self.uploads[fileId])

        return Request(self, fetch)


@pytest.fixture
def configured(monkeypatch):
    state = SimpleNamespace(
        lock=threading.Lock(),
        services=[],
        credentials=[],
        transfers=[],
        active=0,
        peak=0,
        roots=[],
        creates=0,
        discoveries=0,
        transfer_gate=lambda: None,
    )

    def credentials(**kwargs):
        assert kwargs == {
            "token": None,
            "client_id": "client",
            "client_secret": "secret",
            "refresh_token": "drive-token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": drive_module.SCOPES,
        }
        value = SimpleNamespace(owner=threading.get_ident())
        with state.lock:
            state.credentials.append(value)
        return value

    def build(api, version, *, credentials, cache_discovery):
        assert (api, version, cache_discovery) == ("drive", "v3", False)
        service = Service(state, credentials)
        with state.lock:
            state.services.append(service)
        return service

    monkeypatch.setattr(drive_module, "Credentials", credentials)
    monkeypatch.setattr(drive_module, "build", build)
    config = SimpleNamespace(
        google_client_id="client",
        google_client_secret="secret",
        gdrive_refresh_token="drive-token",
        youtube_refresh_token="not-the-drive-token",
    )
    state.client = DriveClient.from_config(config)
    return state


def prepare_uploads(state, monkeypatch, tmp_path, count):
    # Leave upload_file, _write, _serialized and get_file entirely intact.
    monkeypatch.setattr(
        state.client,
        "_file_tags",
        lambda parent, name: {
            "app": "mypage48",
            "role": "asset",
            "archive_key": "recording",
            "file_key": name,
        },
    )
    monkeypatch.setattr(state.client, "_find_child", lambda *args: None)
    paths = []
    for index in range(count):
        path = tmp_path / f"video-{index}.mp4"
        path.write_bytes(f"tiny video {index}".encode())
        paths.append(path)
    return paths


def test_five_real_uploads_use_independent_thread_local_transports(
    configured, monkeypatch, tmp_path
):
    state = configured
    paths = prepare_uploads(state, monkeypatch, tmp_path, 5)
    chunks = threading.Barrier(5, timeout=TIMEOUT)
    state.transfer_gate = chunks.wait

    def upload(path):
        service = state.client.service
        operation_lock = state.client._operation_lock()
        result = state.client.upload_file("archive", path)
        assert state.client.service is service
        assert state.client._operation_lock() is operation_lock
        return result, operation_lock

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(upload, path) for path in paths]
        results = [future.result(timeout=TIMEOUT * 2) for future in futures]

    assert {result["id"] for result, _ in results} == {p.name for p in paths}
    assert state.peak == 5
    assert state.active == 0
    assert len({id(lock) for _, lock in results}) == 5
    assert len({service.owner for service in state.transfers}) == 5
    assert len({id(service) for service in state.transfers}) == 5
    assert len({id(service.transport) for service in state.transfers}) == 5
    assert len({id(service.credentials) for service in state.transfers}) == 5
    # from_config eagerly builds one extra service in the calling thread.
    assert len(state.services) == len(state.credentials) == 6
    assert state.client.service is state.services[0]
    assert state.services[0] not in state.transfers


def test_metadata_completes_while_upload_chunk_is_blocked(
    configured, monkeypatch, tmp_path
):
    state = configured
    path = prepare_uploads(state, monkeypatch, tmp_path, 1)[0]
    entered = threading.Event()
    release = threading.Event()

    def blocked_chunk():
        entered.set()
        assert release.wait(TIMEOUT), "test did not release the blocked upload"

    state.transfer_gate = blocked_chunk
    with ThreadPoolExecutor(max_workers=2) as executor:
        upload = executor.submit(state.client.upload_file, "archive", path)
        try:
            assert entered.wait(TIMEOUT), "upload did not reach next_chunk"
            metadata = executor.submit(state.client.get_file, "metadata")
            assert metadata.result(timeout=TIMEOUT) == {"id": "metadata"}
            assert not release.is_set()
            assert not upload.done()
        finally:
            release.set()
        assert upload.result(timeout=TIMEOUT)["id"] == path.name
    assert len(state.services) == len(state.credentials) == 3
    assert len({service.owner for service in state.services}) == 3


def test_concurrent_root_discovery_creates_only_once(configured, monkeypatch):
    state = configured
    contenders = threading.Barrier(5, timeout=TIMEOUT)
    root_lock = state.client._root_lock

    class ContendedRootLock:
        def __enter__(self):
            # All callers reach the real root lock before any can discover/create.
            contenders.wait()
            root_lock.acquire()

        def __exit__(self, *exc):
            root_lock.release()

    monkeypatch.setattr(state.client, "_root_lock", ContendedRootLock())
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(state.client.ensure_root) for _ in range(5)]
        roots = [future.result(timeout=TIMEOUT * 2) for future in futures]

    assert [root["id"] for root in roots] == ["managed-root"] * 5
    assert state.creates == 1
    # Each caller discovers tagged roots and verifies scoped root membership.
    assert state.discoveries == 10
    assert len(state.roots) == 1
    assert len(state.services) == len(state.credentials) == 6


def test_backup_pool_does_not_starve_youtube_default_executor(tmp_path, monkeypatch):
    config = SimpleNamespace(
        backup_to_gdrive=True,
        gdrive_max_concurrent_uploads=5,
        recordings_dir=tmp_path / "recordings",
        logs_dir=tmp_path / "logs",
    )
    config.recordings_dir.mkdir()
    folders = []
    for index in range(5):
        folder = config.recordings_dir / f"recording-{index}"
        folder.mkdir()
        (folder / ".r2_done").touch()
        folders.append(folder)

    async def exercise():
        loop = asyncio.get_running_loop()
        # asyncio.run owns and shuts down this loop and its default executor.
        loop.set_default_executor(
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="youtube-default")
        )
        all_active = asyncio.Event()
        release = threading.Event()
        lock = threading.Lock()
        active = 0
        peak = 0
        seen = []
        timed_out = []
        metadata_threads = []

        def backup(folder):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
                seen.append((folder, threading.current_thread().name))
                if active == 5:
                    loop.call_soon_threadsafe(all_active.set)
            try:
                if not release.wait(TIMEOUT * 3):
                    with lock:
                        timed_out.append(folder)
            finally:
                with lock:
                    active -= 1

        def get_file(file_id):
            metadata_threads.append(threading.current_thread().name)
            return {"id": file_id}

        fake_client = SimpleNamespace(get_file=get_file)
        worker = BackupWorker(config, fake_client)
        youtube = YouTubeWorker(config, fake_client)
        monkeypatch.setattr(worker, "_backup", backup)
        scan = asyncio.create_task(worker.scan_once())
        try:
            await asyncio.wait_for(all_active.wait(), TIMEOUT)
            result = await asyncio.wait_for(
                youtube._call(fake_client.get_file, "metadata"), TIMEOUT
            )
            assert result == {"id": "metadata"}
            assert not release.is_set()
            assert not scan.done()
            with lock:
                assert active == peak == 5
        finally:
            release.set()
            await asyncio.wait_for(scan, TIMEOUT)

        assert active == 0
        assert peak == 5
        assert not timed_out
        assert {folder for folder, _ in seen} == set(folders)
        assert len(seen) == len({name for _, name in seen}) == 5
        assert all(name.startswith("gdrive-backup") for _, name in seen)
        assert len(metadata_threads) == 1
        assert metadata_threads[0].startswith("youtube-default")
        assert metadata_threads[0] not in {name for _, name in seen}
        assert not worker._retries

    asyncio.run(exercise())


class ReadinessDrive:
    """Only archive discovery and JSON reads are allowed before readiness."""

    def __init__(self, marker, *, include_manifest=True):
        key = "a" * 64
        self.folder = {
            "id": "archive",
            "name": "recording",
            "appProperties": {"archive_key": key},
        }
        self.manifest = validate_manifest(
            {
                "schema_version": 1,
                "archive_key": key,
                "live_id": "live1",
                "platform": "showroom",
                "recording_folder": "recording",
                "metadata_filename": "live1.json",
                "files": [
                    {
                        "id": role,
                        "name": name,
                        "role": role,
                        "size": 1,
                        "md5Checksum": "0" * 32,
                    }
                    for role, name in (
                        ("metadata", "live1.json"),
                        ("video", "live1.mp4"),
                    )
                ],
            }
        )
        self.json_values = {}
        if include_manifest:
            self.json_values[MANIFEST_NAME] = self.manifest
        if marker is not None:
            self.json_values[READY_NAME] = {"archive_key": key, **marker}
        self.calls = []
        self.downloads = []

    def ensure_archive(self, key, name):
        assert key == self.folder["appProperties"]["archive_key"]
        assert name == self.folder["name"]
        self.calls.append(("ensure", key))
        return copy.deepcopy(self.folder)

    def list_children(self, folder_id):
        assert folder_id == self.folder["id"]
        self.calls.append(("children", folder_id))
        return [
            *copy.deepcopy(self.manifest["files"]),
            *({"id": name, "name": name} for name in self.json_values),
        ]

    def get_json(self, file_id):
        self.calls.append(("json", file_id))
        return copy.deepcopy(self.json_values[file_id])

    def download_file(self, *args, **kwargs):
        self.downloads.append((args, kwargs))
        pytest.fail("An unpublished archive must never be downloaded")


@pytest.mark.parametrize(
    "marker, include_manifest",
    [(None, True), ({"schema_version": 1}, False)],
    ids=["missing-ready", "missing-manifest"],
)
def test_youtube_load_skips_unpublished_archive(tmp_path, marker, include_manifest):
    drive = ReadinessDrive(marker, include_manifest=include_manifest)
    worker = YouTubeWorker(
        SimpleNamespace(
            logs_dir=tmp_path / "logs", recordings_dir=tmp_path / "recordings"
        ),
        drive,
    )

    assert asyncio.run(worker._load(drive.folder)) is None
    assert [call[0] for call in drive.calls] == ["ensure", "children"]
    assert not drive.downloads
    assert not worker.staging.exists()
    assert not worker._active


@pytest.mark.parametrize(
    "marker",
    [{"schema_version": 0, "quarantined": True}, {}],
    ids=["quarantined-schema-zero", "incomplete-ready"],
)
def test_youtube_load_rejects_invalid_ready_marker(tmp_path, marker):
    drive = ReadinessDrive(marker)
    worker = YouTubeWorker(
        SimpleNamespace(
            logs_dir=tmp_path / "logs", recordings_dir=tmp_path / "recordings"
        ),
        drive,
    )

    with pytest.raises(DriveSafetyError, match="Ready marker does not match archive"):
        asyncio.run(worker._load(drive.folder))
    assert drive.calls[-2:] == [("json", READY_NAME), ("json", MANIFEST_NAME)]
    assert not drive.downloads
    assert not worker.staging.exists()
    assert not worker._active
