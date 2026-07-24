import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from src.auth.schemas import UserCurrent
from src.config import Settings
from src.dependencies import get_replay_service, require_admin
from src.main import app
from src.replay.exceptions import ReplayAlreadyExists, ReplayUploadError
from src.replay.schemas import ReplayResponse
from src.replay.service import ReplayService


class MockReplayRepository:
    def __init__(self):
        self.insert = AsyncMock()
        self.find_by_live_id = AsyncMock()
        self.find_all = AsyncMock()
        self.count = AsyncMock(return_value=0)
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
        live_history_repo=AsyncMock(),
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
    metadata = json.dumps(
        {
            "live_id": live_id,
            "platform": "SHOWROOM",
            "status": "completed",
            "member_name": "Fahira",
            "member_nickname": "Fahira",
            "duration_seconds": 3600,
        }
    ).encode()

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
    metadata = json.dumps(
        {
            "live_id": "test-live",
            "status": "interrupted",
        }
    ).encode()

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
    metadata = json.dumps(
        {
            "live_id": "existing-live",
            "status": "completed",
        }
    ).encode()

    with pytest.raises(ReplayAlreadyExists, match="already exists"):
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
    now_utc = datetime.now(timezone.utc)
    now_wib = now_utc.astimezone(timezone(timedelta(hours=7)))
    replay_service.repository.count.return_value = 1
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
            "start_at": now_utc,
            "recording_started_at": now_utc,
            "recording_ended_at": now_utc,
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
            "created_at": now_utc,
            "updated_at": now_utc,
        },
    ]

    res = await replay_service.list_all()
    docs = res.data
    meta = res.meta

    assert len(docs) == 1
    assert docs[0].youtube_id == ""
    assert docs[0].title == "Test 1"
    assert docs[0].youtube_title is None
    assert docs[0].member == "Fahira"
    assert docs[0].date == now_wib.strftime("%Y-%m-%d %H:%M WIB")
    assert docs[0].platform == "SHOWROOM"
    assert docs[0].live_id == "live-1"
    assert meta.total_data == 1
    assert meta.current_page == 1
    assert meta.per_page == 20


@pytest.mark.asyncio
async def test_list_all_empty(replay_service):
    replay_service.repository.count.return_value = 0
    replay_service.repository.find_all.return_value = []
    res = await replay_service.list_all()
    assert res.data == []
    assert res.meta.total_data == 0



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
    replay_service.storage.get_file.assert_called_with("replay/live-1/live-1.srt")


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
        live_history_repo=AsyncMock(),
        storage_repository=MockStorageRepository(),
        config=MagicMock(spec=Settings),
    )
    now_utc = datetime.now(timezone.utc)
    now_wib = now_utc.astimezone(timezone(timedelta(hours=7)))
    mock_replay_repo.count.return_value = 1

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
            "start_at": now_utc,
            "recording_started_at": now_utc,
            "recording_ended_at": now_utc,
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
            "created_at": now_utc,
            "updated_at": now_utc,
        }
    ]


    try:
        res = await client.get("/api/replays")
        assert res.status_code == 200
        result = res.json()
        assert "data" in result
        assert "meta" in result
        data = result["data"]
        assert len(data) == 1
        assert data[0]["youtube_id"] == ""
        assert data[0]["title"] == "Test Live"
        assert data[0]["youtube_title"] is None
        assert data[0]["member"] == "Fahira"
        assert data[0]["date"] == now_wib.strftime("%Y-%m-%d %H:%M WIB")
        assert data[0]["platform"] == "SHOWROOM"
        assert data[0]["live_id"] == "live-1"
        assert "srt_file" not in data[0]
        assert data[0]["added_at"].endswith("Z")
    finally:
        app.dependency_overrides.pop(get_replay_service, None)


async def test_replay_list_empty(client: AsyncClient, mock_replay_repo):
    """GET /replays returns empty list."""
    app.dependency_overrides[get_replay_service] = lambda: ReplayService(
        repository=mock_replay_repo,
        live_history_repo=AsyncMock(),
        storage_repository=MockStorageRepository(),
        config=MagicMock(spec=Settings),
    )
    mock_replay_repo.count.return_value = 0
    mock_replay_repo.find_all.return_value = []

    try:
        res = await client.get("/api/replays")
        assert res.status_code == 200
        result = res.json()
        assert result["data"] == []
        assert result["meta"]["total_data"] == 0
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
        live_history_repo=AsyncMock(),
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
        live_history_repo=AsyncMock(),
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
    assert res.status_code == 404


async def test_replay_upload_forbidden(client: AsyncClient, create_user):
    """POST /admin/replay/upload returns 403 for non-admin."""
    _, _, headers = await create_user("regular_user", is_admin=False)
    res = await client.post("/api/admin/replay/upload", headers=headers)
    assert res.status_code == 404


async def test_replay_upload_success(
    client: AsyncClient, create_user, mock_replay_repo, mock_storage_repo
):
    """POST /admin/replay/upload succeeds with admin + valid data."""
    _, _, headers = await create_user("admin_replay", is_admin=True)

    app.dependency_overrides[get_replay_service] = lambda: ReplayService(
        repository=mock_replay_repo,
        live_history_repo=AsyncMock(),
        storage_repository=mock_storage_repo,
        config=MagicMock(spec=Settings),
    )

    mock_replay_repo.exists.return_value = False
    mock_replay_repo.insert.return_value = "mock_id_456"

    metadata = json.dumps(
        {
            "live_id": "upload-test-live",
            "platform": "IDN",
            "status": "completed",
            "member_name": "Fahira",
            "member_nickname": "Fahira",
            "duration_seconds": 1800,
        }
    )

    try:
        res = await client.post(
            "/api/admin/replay/upload",
            headers=headers,
            data={"metadata": metadata},
            files=[
                ("thumbnail", ("thumb.jpg", b"fake_thumb", "image/jpeg")),
                (
                    "jsonl",
                    (
                        "chat.jsonl",
                        b'{"name":"A","message":"hi"}',
                        "application/x-ndjson",
                    ),
                ),
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


async def test_replay_upload_invalid_metadata(client: AsyncClient, create_user):
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


async def test_replay_detail_showroom_free_paid_split(
    client: AsyncClient, mock_replay_repo
):
    """GET /replays/{live_id} returns correct free/paid split for showroom."""
    mock_storage = MockStorageRepository()
    mock_replay_repo.find_by_live_id.return_value = {
        "_id": "r_showroom_split",
        "live_id": "sr-split-001",
        "platform": "showroom",
        "room_id": "12345",
        "member_name": "Fahira",
        "member_nickname": "Fahira",
        "title": "Showroom Live",
        "status": "completed",
        "duration_seconds": 3600,
        "files": {"screenshots": []},
        "chats": [
            {
                "type": "gift",
                "gift_name": "Star",
                "num": 1,
                "total_point": 10,
                "free": False,
                "image": "https://img.sr/star.png",
                "name": "Alice",
                "avatar_url": "https://avatar.sr/alice.jpg",
                "created_at": 100,
            },
            {
                "type": "gift",
                "gift_name": "Heart",
                "num": 3,
                "total_point": 30,
                "free": True,
                "image": "https://img.sr/heart.png",
                "name": "Alice",
                "avatar_url": "https://avatar.sr/alice.jpg",
                "created_at": 200,
            },
            {
                "type": "gift",
                "gift_name": "Star",
                "num": 2,
                "total_point": 20,
                "free": False,
                "image": "https://img.sr/star.png",
                "name": "Bob",
                "created_at": 300,
            },
            {
                "type": "gift",
                "gift_name": "Rainbow",
                "num": 1,
                "total_point": 100,
                "free": True,
                "image": "https://img.sr/rainbow.png",
                "name": "Bob",
                "created_at": 400,
            },
            {
                "type": "chat",
                "message": "hello",
                "name": "Charlie",
                "created_at": 500,
            },
        ],
        "created_at": "2026-07-04T00:00:00Z",
        "updated_at": "2026-07-04T00:00:00Z",
    }

    live_history_repo = AsyncMock()
    live_history_repo.get_global_history_by_live_id.return_value = None

    app.dependency_overrides[get_replay_service] = lambda: ReplayService(
        repository=mock_replay_repo,
        storage_repository=mock_storage,
        live_history_repo=live_history_repo,
        config=MagicMock(spec=Settings),
    )

    try:
        res = await client.get("/api/replays/sr-split-001")
        assert res.status_code == 200
        data = res.json()

        # Aggregate counts
        assert data["total_gifts"] == 3  # paid: 1 + 2
        assert data["total_free_gifts"] == 4  # free: 3 + 1
        assert data["total_gold"] == 30  # paid: 10 + 20
        assert data["total_chats"] == 1  # only the chat message

        # top_fans sorted by total_gold DESC
        fans = data["top_fans"]
        assert len(fans) == 2
        assert fans[0]["user"] == "Bob"
        assert fans[0]["total_gold"] == 20
        assert fans[0]["count"] == 2
        assert fans[0]["free_gold"] == 100
        assert fans[0]["free_count"] == 1

        assert fans[1]["user"] == "Alice"
        assert fans[1]["total_gold"] == 10
        assert fans[1]["count"] == 1
        assert fans[1]["free_gold"] == 30
        assert fans[1]["free_count"] == 3

        # top_gifts deduplicated by name (free/paid count combined)
        gifts = data["top_gifts"]
        assert len(gifts) == 3
        star = next(g for g in gifts if g["name"] == "Star")
        assert star["count"] == 3
        assert star["total_gold"] == 30
        assert star["free"] is False  # first occurrence was paid
    finally:
        app.dependency_overrides.pop(get_replay_service, None)


async def test_replay_detail_idn_basic(client: AsyncClient, mock_replay_repo):
    """GET /replays/{live_id} works for IDN (no free/paid split)."""
    mock_storage = MockStorageRepository()
    mock_replay_repo.find_by_live_id.return_value = {
        "_id": "r_idn_basic",
        "live_id": "idn-basic-001",
        "platform": "idn",
        "room_identifier": "room-abc",
        "member_name": "Feni",
        "member_nickname": "Feni",
        "title": "IDN Live",
        "status": "completed",
        "duration_seconds": 1800,
        "files": {"screenshots": []},
        "chats": [
            {
                "user": {"name": "Alice", "avatar_url": "https://avatar.idn/alice.jpg"},
                "gift": {"name": "Gold", "gold": 50},
            },
            {
                "user": {"name": "Bob", "avatar_url": "https://avatar.idn/bob.jpg"},
                "gift": {"name": "Silver", "gold": 30},
            },
            {"user": {"name": "Charlie"}, "chat": "Nice stream!"},
        ],
        "created_at": "2026-07-04T00:00:00Z",
        "updated_at": "2026-07-04T00:00:00Z",
    }

    live_history_repo = AsyncMock()
    live_history_repo.get_global_history_by_live_id.return_value = None

    app.dependency_overrides[get_replay_service] = lambda: ReplayService(
        repository=mock_replay_repo,
        storage_repository=mock_storage,
        live_history_repo=live_history_repo,
        config=MagicMock(spec=Settings),
    )

    try:
        res = await client.get("/api/replays/idn-basic-001")
        assert res.status_code == 200
        data = res.json()

        assert data["total_gifts"] == 2
        assert data["total_free_gifts"] == 0
        assert data["total_gold"] == 80
        assert data["total_chats"] == 1

        fans = data["top_fans"]
        assert len(fans) == 2
        assert fans[0]["total_gold"] == 50
        assert fans[1]["total_gold"] == 30
        # IDN top_fans should have no free fields (defaults to 0)
        assert "free_gold" in fans[0]
        assert fans[0]["free_gold"] == 0
        assert fans[0]["free_count"] == 0
    finally:
        app.dependency_overrides.pop(get_replay_service, None)


async def test_update_youtube_data_admin(client: AsyncClient, mock_replay_repo):
    """PATCH /admin/replay/{live_id}/youtube requires admin and calls service."""
    mock_storage = MockStorageRepository()
    mock_replay_repo.update_youtube_data = AsyncMock(return_value=True)

    app.dependency_overrides[get_replay_service] = lambda: ReplayService(
        repository=mock_replay_repo,
        storage_repository=mock_storage,
        live_history_repo=AsyncMock(),
        config=MagicMock(spec=Settings),
    )

    app.dependency_overrides[require_admin] = lambda: UserCurrent(
        id="admin_123",
        userId="admin_123",
        username="admin",
        name="admin",
        email="admin@test.com",
        isAdmin=True,
    )

    try:
        res = await client.patch(
            "/api/admin/replay/test-live-123/youtube",
            json={"youtube_id": "xyz123", "youtube_title": "Test YouTube Title"},
        )
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}

        mock_replay_repo.update_youtube_data.assert_called_once_with(
            "test-live-123", "xyz123", "Test YouTube Title"
        )

        mock_replay_repo.update_youtube_data.return_value = False
        res2 = await client.patch(
            "/api/admin/replay/test-live-123/youtube",
            json={"youtube_id": "xyz123", "youtube_title": "Title"},
        )
        assert res2.status_code == 404
    finally:
        app.dependency_overrides.pop(get_replay_service, None)
        app.dependency_overrides.pop(require_admin, None)
