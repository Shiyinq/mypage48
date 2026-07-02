import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, ANY
from httpx import AsyncClient

from src.replay.service import ReplayService
from src.replay.schemas import ReplayListItem, ReplayResponse
from src.replay.exceptions import ReplayUploadError
from src.dependencies import get_replay_service, get_current_user
from src.main import app
from src.config import Settings


class MockReplayRepository:
    def __init__(self):
        self.insert = AsyncMock()
        self.find_by_live_id = AsyncMock()
        self.find_all = AsyncMock()
        self.exists = AsyncMock(return_value=False)


class MockStorageRepository:
    def __init__(self):
        self.upload_file = AsyncMock()
        self.get_file = AsyncMock()


@pytest.fixture
def mock_replay_repo():
    return MockReplayRepository()


@pytest.fixture
def mock_storage_repo():
    return MockStorageRepository()


@pytest.fixture
def replay_service(mock_replay_repo, mock_storage_repo):
    mock_config = MagicMock(spec=Settings)
    return ReplayService(
        repository=mock_replay_repo,
        storage_repository=mock_storage_repo,
        config=mock_config,
    )


# ---------------------------------------------------------------------------
# Service unit tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upload_success(replay_service):
    replay_service.repository.exists.return_value = False
    replay_service.repository.insert.return_value = "mock_id_123"

    live_id = "test-live-001"
    metadata = json.dumps({
        "live_id": live_id,
        "platform": "SHOWROOM",
        "status": "completed",
        "member_name": "Fahira",
        "member_nickname": "Fahira",
        "duration_seconds": 3600,
    }).encode()

    result = await replay_service.upload(
        live_id=live_id,
        metadata_bytes=metadata,
        thumbnail_bytes=b"fake_thumb",
        jsonl_bytes=b'{"name":"Alice","message":"hello"}\n{"name":"Bob","message":"hi"}',
        srt_bytes=b"1\n00:00:01,000 --> 00:00:02,000\nHello",
        screenshot_bytes_list=[("shot1.jpg", b"shot1_data")],
    )

    assert isinstance(result, ReplayResponse)
    assert result.live_id == live_id
    assert result.platform == "SHOWROOM"
    assert result.member_name == "Fahira"
    assert result.duration_seconds == 3600
    assert len(result.chats) == 2
    assert len(result.files.screenshots) == 1
    replay_service.repository.insert.assert_called_once()
    replay_service.storage.upload_file.assert_called()


@pytest.mark.asyncio
async def test_upload_invalid_metadata(replay_service):
    with pytest.raises(ReplayUploadError, match="Invalid metadata JSON"):
        await replay_service.upload(
            live_id="test",
            metadata_bytes=b"not-json",
            thumbnail_bytes=b"",
            jsonl_bytes=b"",
            srt_bytes=b"",
            screenshot_bytes_list=[],
        )


@pytest.mark.asyncio
async def test_upload_non_completed_status(replay_service):
    metadata = json.dumps({
        "live_id": "test-live",
        "status": "interrupted",
    }).encode()

    with pytest.raises(ReplayUploadError, match="Only 'completed' allowed"):
        await replay_service.upload(
            live_id="test-live",
            metadata_bytes=metadata,
            thumbnail_bytes=b"",
            jsonl_bytes=b"",
            srt_bytes=b"",
            screenshot_bytes_list=[],
        )


@pytest.mark.asyncio
async def test_upload_already_exists(replay_service):
    replay_service.repository.exists.return_value = True
    metadata = json.dumps({
        "live_id": "existing-live",
        "status": "completed",
    }).encode()

    with pytest.raises(ReplayUploadError, match="already exists"):
        await replay_service.upload(
            live_id="existing-live",
            metadata_bytes=metadata,
            thumbnail_bytes=b"",
            jsonl_bytes=b"",
            srt_bytes=b"",
            screenshot_bytes_list=[],
        )


@pytest.mark.asyncio
async def test_list_all(replay_service):
    now = datetime.now(timezone.utc)
    replay_service.repository.find_all.return_value = [
        {
            "_id": "id1",
            "live_id": "live-1",
            "platform": "SHOWROOM",
            "room_id": None,
            "room_identifier": None,
            "title": "Test 1",
            "member_name": "Fahira",
            "member_nickname": "Fahira",
            "status": "completed",
            "start_at": now,
            "recording_started_at": now,
            "recording_ended_at": now,
            "duration_seconds": 3600,
            "srt_file": None,
            "youtube_id": None,
            "files": {
                "json_file": "replay/live-1/live-1.json",
                "thumbnail": "replay/live-1/live-1.jpg",
                "jsonl": "replay/live-1/live-1.jsonl",
                "srt": "replay/live-1/live-1.srt",
                "screenshots": ["shot1.jpg"],
            },
            "chats": [{"name": "Alice", "message": "hi"}],
            "created_at": now,
            "updated_at": now,
        },
    ]

    docs = await replay_service.list_all()

    assert len(docs) == 1
    assert docs[0]["live_id"] == "live-1"
    assert docs[0]["member"] == "Fahira"
    assert "member_name" not in docs[0]


@pytest.mark.asyncio
async def test_list_all_empty(replay_service):
    replay_service.repository.find_all.return_value = []
    docs = await replay_service.list_all()
    assert docs == []


@pytest.mark.asyncio
async def test_get_srt_content_success(replay_service):
    replay_service.repository.find_by_live_id.return_value = {
        "files": {
            "srt": "replay/live-1/live-1.srt",
        }
    }
    replay_service.storage.get_file.return_value = (
        b"1\n00:00:01,000 --> 00:00:02,000\nHello"
    )

    content = await replay_service.get_srt_content("live-1")
    assert content == "1\n00:00:01,000 --> 00:00:02,000\nHello"
    replay_service.storage.get_file.assert_called_with(
        "replay/live-1/live-1.srt"
    )


@pytest.mark.asyncio
async def test_get_srt_content_not_found(replay_service):
    replay_service.repository.find_by_live_id.return_value = None
    content = await replay_service.get_srt_content("nonexistent")
    assert content is None


@pytest.mark.asyncio
async def test_get_srt_content_no_srt_path(replay_service):
    replay_service.repository.find_by_live_id.return_value = {"files": {}}
    content = await replay_service.get_srt_content("live-1")
    assert content is None


@pytest.mark.asyncio
async def test_get_srt_content_storage_failure(replay_service):
    replay_service.repository.find_by_live_id.return_value = {
        "files": {"srt": "replay/live-1/live-1.srt"}
    }
    replay_service.storage.get_file.return_value = None
    content = await replay_service.get_srt_content("live-1")
    assert content is None


# ---------------------------------------------------------------------------
# API integration tests
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.asyncio


async def test_replay_list_success(client: AsyncClient, mock_replay_repo):
    """GET /replays returns list of replays."""
    app.dependency_overrides[get_replay_service] = lambda: ReplayService(
        repository=mock_replay_repo,
        storage_repository=MockStorageRepository(),
        config=MagicMock(spec=Settings),
    )
    now = datetime.now(timezone.utc)
    mock_replay_repo.find_all.return_value = [
        {
            "_id": "r1",
            "live_id": "live-1",
            "platform": "SHOWROOM",
            "room_id": None,
            "room_identifier": None,
            "title": "Test Live",
            "member_name": "Fahira",
            "member_nickname": "Fahira",
            "status": "completed",
            "start_at": now,
            "recording_started_at": now,
            "recording_ended_at": now,
            "duration_seconds": 3600,
            "srt_file": "live-1.srt",
            "youtube_id": None,
            "files": {
                "json_file": "replay/live-1/live-1.json",
                "thumbnail": "replay/live-1/live-1.jpg",
                "jsonl": "replay/live-1/live-1.jsonl",
                "srt": "replay/live-1/live-1.srt",
                "screenshots": [],
            },
            "chats": [{"name": "Alice", "message": "hi"}],
            "created_at": now,
            "updated_at": now,
        }
    ]

    try:
        res = await client.get("/api/replays")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["live_id"] == "live-1"
        assert data[0]["member"] == "Fahira"
        assert data[0]["member_nickname"] == "Fahira"
        assert "chats" not in data[0]
        assert data[0]["duration_seconds"] == 3600
        assert data[0]["created_at"].endswith("Z")
    finally:
        app.dependency_overrides.pop(get_replay_service, None)


async def test_replay_list_empty(client: AsyncClient, mock_replay_repo):
    """GET /replays returns empty list."""
    app.dependency_overrides[get_replay_service] = lambda: ReplayService(
        repository=mock_replay_repo,
        storage_repository=MockStorageRepository(),
        config=MagicMock(spec=Settings),
    )
    mock_replay_repo.find_all.return_value = []

    try:
        res = await client.get("/api/replays")
        assert res.status_code == 200
        assert res.json() == []
    finally:
        app.dependency_overrides.pop(get_replay_service, None)


async def test_replay_srt_success(client: AsyncClient, mock_replay_repo):
    """GET /replays/{live_id}/srt returns SRT text."""
    mock_storage = MockStorageRepository()
    mock_storage.get_file.return_value = b"1\n00:00:01,000 --> 00:00:02,000\nHello"
    mock_replay_repo.find_by_live_id.return_value = {
        "files": {"srt": "replay/live-1/live-1.srt"}
    }

    app.dependency_overrides[get_replay_service] = lambda: ReplayService(
        repository=mock_replay_repo,
        storage_repository=mock_storage,
        config=MagicMock(spec=Settings),
    )

    try:
        res = await client.get("/api/replays/live-1/srt")
        assert res.status_code == 200
        assert res.text == "1\n00:00:01,000 --> 00:00:02,000\nHello"
        assert res.headers["content-type"].startswith("text/plain")
    finally:
        app.dependency_overrides.pop(get_replay_service, None)


async def test_replay_srt_not_found(client: AsyncClient, mock_replay_repo):
    """GET /replays/{live_id}/srt returns 404 when replay not found."""
    mock_replay_repo.find_by_live_id.return_value = None

    app.dependency_overrides[get_replay_service] = lambda: ReplayService(
        repository=mock_replay_repo,
        storage_repository=MockStorageRepository(),
        config=MagicMock(spec=Settings),
    )

    try:
        res = await client.get("/api/replays/nonexistent/srt")
        assert res.status_code == 404
    finally:
        app.dependency_overrides.pop(get_replay_service, None)


async def test_replay_upload_unauthorized(client: AsyncClient):
    """POST /admin/replay/upload returns 401 without auth."""
    res = await client.post("/api/admin/replay/upload")
    assert res.status_code == 401


async def test_replay_upload_forbidden(client: AsyncClient, create_user):
    """POST /admin/replay/upload returns 403 for non-admin."""
    _, _, headers = await create_user("regular_user", is_admin=False)
    res = await client.post(
        "/api/admin/replay/upload", headers=headers
    )
    assert res.status_code == 403


async def test_replay_upload_success(
    client: AsyncClient, create_user, mock_replay_repo, mock_storage_repo
):
    """POST /admin/replay/upload succeeds with admin + valid data."""
    _, _, headers = await create_user("admin_replay", is_admin=True)

    app.dependency_overrides[get_replay_service] = lambda: ReplayService(
        repository=mock_replay_repo,
        storage_repository=mock_storage_repo,
        config=MagicMock(spec=Settings),
    )

    mock_replay_repo.exists.return_value = False
    mock_replay_repo.insert.return_value = "mock_id_456"

    metadata = json.dumps({
        "live_id": "upload-test-live",
        "platform": "IDN",
        "status": "completed",
        "member_name": "Fahira",
        "member_nickname": "Fahira",
        "duration_seconds": 1800,
    })

    try:
        res = await client.post(
            "/api/admin/replay/upload",
            headers=headers,
            data={"metadata": metadata},
            files=[
                ("thumbnail", ("thumb.jpg", b"fake_thumb", "image/jpeg")),
                ("jsonl", ("chat.jsonl", b'{"name":"A","message":"hi"}', "application/x-ndjson")),
                ("srt", ("sub.srt", b"1\n00:00:01 --> 00:00:02\nHi", "text/plain")),
            ],
        )
        assert res.status_code == 200
        data = res.json()
        assert data["live_id"] == "upload-test-live"
        assert data["platform"] == "IDN"
        assert data["member_name"] == "Fahira"
        assert data["duration_seconds"] == 1800
        assert len(data["chats"]) == 1
    finally:
        app.dependency_overrides.pop(get_replay_service, None)


async def test_replay_upload_invalid_metadata(
    client: AsyncClient, create_user
):
    """POST /admin/replay/upload returns error for invalid metadata JSON."""
    _, _, headers = await create_user("admin_replay2", is_admin=True)

    res = await client.post(
        "/api/admin/replay/upload",
        headers=headers,
        data={"metadata": "not-json"},
        files=[
            ("thumbnail", ("thumb.jpg", b"data", "image/jpeg")),
            ("jsonl", ("chat.jsonl", b"{}", "application/x-ndjson")),
            ("srt", ("sub.srt", b"", "text/plain")),
        ],
    )
    assert res.status_code == 500
