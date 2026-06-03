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
async def test_get_global_history(client: AsyncClient, db):
    """Test getting global live history."""
    # Assuming there are no lives initially or we just test the endpoint structure
    response = await client.get("/api/history/lives")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "total_pages" in data
