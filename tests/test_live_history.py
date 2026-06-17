import datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_update_live_history_success(client: AsyncClient, db, create_user):
    """Test updating live watch history."""
    token, user_id, headers = await create_user("livehistoryuser")

    payload = {
        "live_id": "live-12345",
        "member_id": "member-xyz",
        "member_name": "Erine Cintaku",
        "member_nickname": "Erine",
        "platform": "showroom",
        "ping_duration": 30,
        "live_title": "Test Title"
    }

    response = await client.post(
        "/api/history/lives/update", json=payload, headers=headers
    )
    assert response.status_code == 204

    # Verify that the history was saved by fetching it
    response_get = await client.get("/api/history/lives/watched", headers=headers)
    assert response_get.status_code == 200
    data = response_get.json()
    assert "data" in data
    assert len(data["data"]) == 1
    assert data["data"][0]["member_name"] == "Erine Cintaku"
    assert data["data"][0]["member_nickname"] == "Erine"
    assert data["data"][0]["duration"] == 30
    assert data["data"][0]["live_title"] == "Test Title"


@pytest.mark.asyncio
async def test_update_live_history_unauthorized(client: AsyncClient, db):
    """Test updating live history without authentication."""
    payload = {
        "live_id": "live-12345",
        "member_id": "member-xyz",
        "member_name": "Erine Cintaku",
        "platform": "showroom",
        "ping_duration": 30,
        "live_title": "Test Title"
    }
    response = await client.post("/api/history/lives/update", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_live_history(client: AsyncClient, db, create_user):
    """Test getting saved live history list."""
    token, user_id, headers = await create_user("gethistoryuser")

    payload1 = {
        "live_id": "live-1",
        "member_id": "m1",
        "member_name": "Jacqueline Immanuela",
        "platform": "showroom",
        "ping_duration": 60,
        "live_title": "Title 1"
    }
    payload2 = {
        "live_id": "live-2",
        "member_id": "m2",
        "member_name": "Feni",
        "platform": "idn",
        "ping_duration": 120,
        "live_title": "Title 2"
    }

    await client.post("/api/history/lives/update", json=payload1, headers=headers)
    await client.post("/api/history/lives/update", json=payload2, headers=headers)

    response = await client.get("/api/history/lives/watched", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert len(data["data"]) >= 2
    
    # It should return the latest updated first (payload2)
    assert data["data"][0]["member_name"] == "Feni"
    assert data["data"][0]["duration"] == 120
    assert data["data"][1]["member_name"] == "Jacqueline Immanuela"


@pytest.mark.asyncio
async def test_get_live_history_stats(client: AsyncClient, db, create_user):
    """Test getting overall live history stats."""
    token, user_id, headers = await create_user("history_stats_user")

    # Add durations
    await client.post("/api/history/lives/update", json={"live_id": "l1", "member_id": "m1", "member_name": "Member 1", "platform": "showroom", "ping_duration": 30}, headers=headers)
    await client.post("/api/history/lives/update", json={"live_id": "l2", "member_id": "m1", "member_name": "Member 1", "platform": "idn", "ping_duration": 60}, headers=headers)
    await client.post("/api/history/lives/update", json={"live_id": "l3", "member_id": "m2", "member_name": "Member 2", "platform": "showroom", "ping_duration": 30}, headers=headers)

    response = await client.get("/api/history/lives/watched/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_duration"] == 120
    assert data["member_counts"]["m1"] == 2
    assert data["member_counts"]["m2"] == 1
    assert data["member_durations"]["m1"] == 90
    assert data["member_durations"]["m2"] == 30
    assert data["platform_counts"]["showroom"] == 2
    assert data["platform_counts"]["idn"] == 1
    
    assert data["longest_watch"] is not None
    assert data["longest_watch"]["duration"] == 60
    assert data["longest_watch"]["platform"] == "idn"
    assert data["longest_watch"]["member_name"] == "Member 1"


@pytest.mark.asyncio
async def test_get_member_stats(client: AsyncClient, db, create_user):
    """Test getting specific member stats."""
    token, user_id, headers = await create_user("member_stats_user")

    await client.post("/api/history/lives/update", json={"live_id": "l1", "member_id": "m1", "member_name": "Member 1", "platform": "showroom", "ping_duration": 45}, headers=headers)
    await client.post("/api/history/lives/update", json={"live_id": "l2", "member_id": "m1", "member_name": "Member 1", "platform": "idn", "ping_duration": 15}, headers=headers)
    
    response = await client.get("/api/history/lives/watched/members/m1/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert data["member_id"] == "m1"
    assert data["total_duration"] == 60
    assert data["total_watches"] == 2
    
    assert data["platform_counts"]["showroom"] == 1
    assert data["platform_counts"]["idn"] == 1
    
    assert data["longest_watch"] is not None
    assert data["longest_watch"]["duration"] == 45
    assert data["longest_watch"]["platform"] == "showroom"


@pytest.mark.asyncio
async def test_get_global_history(client: AsyncClient, db, seed_global_live_history, monkeypatch):
    """Test getting global live history."""
    
    # Mock storage_service resolve_image_variants
    from src.storage.service import StorageService
    async def mock_resolve_image_variants(self, path: str):
        # path is "live/gl1.webp"
        return {
            "url": f"https://mocked-s3.com/{path}",
            "url_medium": f"https://mocked-s3.com/{path.replace('.webp', '_medium.webp')}",
            "url_small": f"https://mocked-s3.com/{path.replace('.webp', '_small.webp')}",
            "blurHash": "U00000000000000000000000000000000000"
        }
    monkeypatch.setattr(StorageService, "resolve_image_variants", mock_resolve_image_variants)

    response = await client.get("/api/history/lives")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "total_pages" in data

    # Check if the variants are resolved for the first item (gl1)
    # The API sorts descending by default, so gl3 is first, gl2 is second, gl1 is third.
    items = data["data"]
    gl1_item = next(item for item in items if item["live_id"] == "gl1")
    assert gl1_item["image"] == "https://mocked-s3.com/live/gl1.webp"
    assert gl1_item["image_medium"] == "https://mocked-s3.com/live/gl1_medium.webp"
    assert gl1_item["image_small"] == "https://mocked-s3.com/live/gl1_small.webp"
    assert gl1_item["blurHash"] == "U00000000000000000000000000000000000"


@pytest.mark.asyncio
async def test_get_watched_live_members_ranking(client: AsyncClient, db, create_user):
    """Test getting watched members ranking."""
    token, user_id, headers = await create_user("ranking_user")

    # Add durations
    await client.post("/api/history/lives/update", json={"live_id": "l1", "member_id": "m1", "member_name": "Member 1", "platform": "showroom", "ping_duration": 30}, headers=headers)
    await client.post("/api/history/lives/update", json={"live_id": "l2", "member_id": "m2", "member_name": "Member 2", "platform": "idn", "ping_duration": 60}, headers=headers)
    await client.post("/api/history/lives/update", json={"live_id": "l3", "member_id": "m1", "member_name": "Member 1", "platform": "showroom", "ping_duration": 30}, headers=headers)

    response = await client.get("/api/history/lives/watched/members/ranking", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert "meta" in data
    
    ranking = data["data"]
    assert len(ranking) == 2
    
    # Member 1 should be first (2 watches)
    assert ranking[0]["member_id"] == "m1"
    assert ranking[0]["total_watches"] == 2
    assert ranking[0]["total_duration"] == 60
    
    # Member 2 should be second (1 watch)
    assert ranking[1]["member_id"] == "m2"
    assert ranking[1]["total_watches"] == 1
    assert ranking[1]["total_duration"] == 60


@pytest.fixture
async def seed_global_live_history(db):
    """Seed the live_history collection with sample global live data."""
    now = datetime.datetime.now(datetime.timezone.utc)
    docs = [
        {
            "live_id": "gl1",
            "platform": "showroom",
            "title": "Showroom Live 1",
            "image": "live/gl1.webp",
            "view_num": 5000,
            "start_at": now - datetime.timedelta(hours=3),
            "end_at": now - datetime.timedelta(hours=2),
            "last_seen_at": now - datetime.timedelta(hours=2),
            "status": "ended",
            "member": {"id": "gm1", "name": "Member Alpha"},
            "duration": 3600,
        },
        {
            "live_id": "gl2",
            "platform": "idn",
            "title": "IDN Live 1",
            "image": None,
            "view_num": 12000,
            "start_at": now - datetime.timedelta(hours=2),
            "end_at": now - datetime.timedelta(hours=1),
            "last_seen_at": now - datetime.timedelta(hours=1),
            "status": "ended",
            "member": {"id": "gm1", "name": "Member Alpha"},
            "duration": 3600,
        },
        {
            "live_id": "gl3",
            "platform": "showroom",
            "title": "Showroom Live 2",
            "image": None,
            "view_num": 8000,
            "start_at": now - datetime.timedelta(hours=1),
            "end_at": now,
            "last_seen_at": now,
            "status": "ended",
            "member": {"id": "gm2", "name": "Member Beta"},
            "duration": 1800,
        },
    ]
    await db["live_history"].insert_many(docs)
    return docs


@pytest.mark.asyncio
async def test_get_global_live_stats(client: AsyncClient, db, seed_global_live_history):
    """Test getting global live history statistics."""
    response = await client.get("/api/history/lives/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_lives"] == 3
    assert data["total_duration"] == 9000  # 3600 + 3600 + 1800
    assert data["unique_members_count"] == 2

    # Top member should be Member Alpha (2 lives)
    assert data["top_member_id"] == "gm1"
    assert data["top_member_name"] == "Member Alpha"
    assert data["top_member_watches"] == 2

    # Platform counts
    assert data["platform_counts"]["showroom"] == 2
    assert data["platform_counts"]["idn"] == 1

    # Highest view live should be IDN Live 1 with 12000 views
    hvl = data["highest_view_live"]
    assert hvl is not None
    assert hvl["duration"] == 12000  # view_num stored in duration field
    assert hvl["live_title"] == "IDN Live 1"
    assert hvl["platform"] == "idn"
    assert hvl["member_name"] == "Member Alpha"


@pytest.mark.asyncio
async def test_get_global_members_ranking(client: AsyncClient, db, seed_global_live_history):
    """Test getting global live members ranking."""
    response = await client.get("/api/history/lives/members/ranking")
    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "meta" in data

    ranking = data["data"]
    assert len(ranking) == 2

    # Member Alpha should be first (2 lives, 7200s total)
    assert ranking[0]["member_id"] == "gm1"
    assert ranking[0]["member_name"] == "Member Alpha"
    assert ranking[0]["total_watches"] == 2
    assert ranking[0]["total_duration"] == 7200

    # Member Beta should be second (1 live, 1800s total)
    assert ranking[1]["member_id"] == "gm2"
    assert ranking[1]["member_name"] == "Member Beta"
    assert ranking[1]["total_watches"] == 1
    assert ranking[1]["total_duration"] == 1800


@pytest.mark.asyncio
async def test_get_global_member_history(client: AsyncClient, db, seed_global_live_history):
    """Test getting global live history for a specific member."""
    response = await client.get("/api/history/lives/members/gm1")
    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert data["total"] == 2
    assert len(data["data"]) == 2

    # Should be sorted by start_at descending (most recent first)
    assert data["data"][0]["live_id"] == "gl2"
    assert data["data"][1]["live_id"] == "gl1"


@pytest.mark.asyncio
async def test_get_global_member_history_empty(client: AsyncClient, db, seed_global_live_history):
    """Test getting global live history for a non-existent member."""
    response = await client.get("/api/history/lives/members/nonexistent")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert len(data["data"]) == 0


@pytest.mark.asyncio
async def test_get_global_member_stats(client, db, seed_global_live_history):
    # Make request for "gm1" which has two lives in the seed
    response = await client.get("/api/history/lives/members/gm1/stats")

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["member_id"] == "gm1"
    assert data["total_duration"] == 7200  # 3600 * 2
    assert data["total_lives"] == 2
    assert "showroom" in data["platform_counts"]
    assert data["platform_counts"]["showroom"] == 1
    assert "idn" in data["platform_counts"]
    assert data["platform_counts"]["idn"] == 1
    
    # Check longest live
    assert data["longest_live"] is not None
    assert data["longest_live"]["duration"] == 3600
    # Both gl1 and gl2 have duration 3600, so longest platform will be one of them (likely IDN or showroom)

@pytest.mark.asyncio
async def test_invalid_date_format(client: AsyncClient, db, create_user):
    """Test getting history with invalid date formats."""
    token, user_id, headers = await create_user("invalid_date_user")

    # Invalid format completely
    response = await client.get("/api/history/lives/watched?start_date=invalid-date", headers=headers)
    assert response.status_code == 400
    assert "INVALID_DATE_FORMAT" in response.json()["detail"]

    # Invalid calendar date (e.g., June 31st)
    response2 = await client.get("/api/history/lives/watched?start_date=2025-06-31", headers=headers)
    assert response2.status_code == 400
    assert "INVALID_DATE_FORMAT" in response2.json()["detail"]

    # Invalid end_date
    response3 = await client.get("/api/history/lives/watched?end_date=2025-13-01", headers=headers)
    assert response3.status_code == 400
    assert "INVALID_DATE_FORMAT" in response3.json()["detail"]

    # Global stats invalid date
    response4 = await client.get("/api/history/lives/stats?start_date=31-juni-2025")
    assert response4.status_code == 400
    assert "INVALID_DATE_FORMAT" in response4.json()["detail"]


@pytest.mark.asyncio
async def test_get_pc_collection_all(client: AsyncClient, db, create_user, seed_global_live_history):
    """Test getting all PC collection cards with ownership status."""
    token, user_id, headers = await create_user("pcuser1")

    # Mark "gl1" as watched (owned)
    payload = {
        "live_id": "gl1",
        "member_id": "gm1",
        "member_name": "Member Alpha",
        "platform": "showroom",
        "ping_duration": 30,
        "live_title": "Showroom Live 1"
    }
    await client.post("/api/history/lives/update", json=payload, headers=headers)

    response = await client.get("/api/history/lives/pc?collection_type=all", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "total" in data
    assert data["total"] == 3
    assert len(data["data"]) == 3

    # Verify ownership assignment
    for item in data["data"]:
        if item["live_id"] == "gl1":
            assert item["is_owned"] is True
        else:
            assert item["is_owned"] is False


@pytest.mark.asyncio
async def test_get_pc_collection_owned(client: AsyncClient, db, create_user, seed_global_live_history):
    """Test getting only owned PC collection cards."""
    token, user_id, headers = await create_user("pcuser2")

    payload = {
        "live_id": "gl2",
        "member_id": "gm1",
        "member_name": "Member Alpha",
        "platform": "idn",
        "ping_duration": 60,
        "live_title": "IDN Live 1"
    }
    await client.post("/api/history/lives/update", json=payload, headers=headers)

    response = await client.get("/api/history/lives/pc?collection_type=owned", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 1
    assert len(data["data"]) == 1
    assert data["data"][0]["live_id"] == "gl2"
    assert data["data"][0]["is_owned"] is True


@pytest.mark.asyncio
async def test_get_pc_collection_unowned(client: AsyncClient, db, create_user, seed_global_live_history):
    """Test getting only unowned PC collection cards."""
    token, user_id, headers = await create_user("pcuser3")

    payload = {
        "live_id": "gl3",
        "member_id": "gm2",
        "member_name": "Member Beta",
        "platform": "showroom",
        "ping_duration": 30,
        "live_title": "Showroom Live 2"
    }
    await client.post("/api/history/lives/update", json=payload, headers=headers)

    response = await client.get("/api/history/lives/pc?collection_type=unowned", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 2
    assert len(data["data"]) == 2
    
    for item in data["data"]:
        assert item["live_id"] != "gl3"
        assert item["is_owned"] is False


@pytest.mark.asyncio
async def test_get_pc_collection_sorting(client: AsyncClient, db, create_user, seed_global_live_history):
    """Test getting PC collection cards with different sort_by parameters."""
    token, user_id, headers = await create_user("pcuser4")

    # Update one live to have more view_num by seeding it manually or it's already seeded
    # seed_global_live_history provides gl1, gl2, gl3 with some data.
    # We will test sort_by=tier_desc which should order by view_num descending

    response = await client.get("/api/history/lives/pc?collection_type=all&sort_by=tier_desc", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] > 0
    # Check if view_num is actually descending
    for i in range(len(data["data"]) - 1):
        assert data["data"][i].get("view_num", 0) >= data["data"][i + 1].get("view_num", 0)

    # Test date_asc
    response = await client.get("/api/history/lives/pc?collection_type=all&sort_by=date_asc", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] > 0
    # Check if start_at is ascending
    for i in range(len(data["data"]) - 1):
        start_1 = data["data"][i].get("start_at")
        start_2 = data["data"][i + 1].get("start_at")
        if start_1 and start_2:
            assert start_1 <= start_2


@pytest.mark.asyncio
async def test_get_pc_collection_unauthenticated(client: AsyncClient, db, seed_global_live_history):
    """Test getting PC collection cards without authentication."""
    # Request without headers (no auth token)
    response = await client.get("/api/history/lives/pc?collection_type=all")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] > 0
    assert len(data["data"]) > 0
    
    # All cards should have is_owned = False for unauthenticated users
    for item in data["data"]:
        assert item["is_owned"] is False
