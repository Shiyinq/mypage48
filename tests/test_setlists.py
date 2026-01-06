import pytest
from httpx import AsyncClient
from datetime import datetime
from src.tickets.schemas import TicketInDB, TicketEvent, TicketSeat


@pytest.mark.asyncio
async def test_get_setlists_unauthorized(client: AsyncClient):
    """Test that unauthorized users cannot access setlists endpoint."""
    response = await client.get("/api/theater/setlists")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_seed_setlists(client: AsyncClient, db):
    """Test seeding the database with JKT48 setlist data."""
    # Seed endpoint is at /api/theater/setlists/seed
    response = await client.post("/api/theater/setlists/seed")
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert "count" in data
    assert data["count"] > 0


@pytest.mark.asyncio
async def test_get_setlists_list(client: AsyncClient, db):
    """Test getting all setlists with authentication."""
    # Seed setlists data
    await client.post("/api/theater/setlists/seed")

    # Register and Login
    register_payload = {
        "fullName": "Setlist User",
        "memberId": "11111",
        "username": "setlistuser",
        "email": "setlist@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "setlistuser"},
        {"$set": {"isEmailVerified": True}}
    )

    login_res = await client.post("/api/auth/signin", data={
        "username": "setlistuser",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get setlists
    response = await client.get("/api/theater/setlists", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "maxAttendance" in data
    assert "setlists" in data
    assert data["total"] > 0
    assert len(data["setlists"]) > 0

    # Check setlist structure
    setlist = data["setlists"][0]
    assert "setlistId" in setlist
    assert "title" in setlist
    assert "imageUrl" in setlist
    assert "description" in setlist
    assert "type" in setlist
    assert "active" in setlist
    assert "watched" in setlist
    assert "count" in setlist["watched"]
    assert "percentage" in setlist["watched"]
    assert "isMostWatched" in setlist["watched"]


@pytest.mark.asyncio
async def test_get_setlists_pagination(client: AsyncClient, db):
    """Test setlists pagination."""
    # Seed setlists data
    await client.post("/api/theater/setlists/seed")

    # Register and Login
    register_payload = {
        "fullName": "Pagination User",
        "memberId": "22222",
        "username": "paginationuser",
        "email": "pagination@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "paginationuser"},
        {"$set": {"isEmailVerified": True}}
    )

    login_res = await client.post("/api/auth/signin", data={
        "username": "paginationuser",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test limit parameter
    response = await client.get("/api/theater/setlists?limit=5", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["setlists"]) <= 5

    # Test skip parameter
    response_skip = await client.get("/api/theater/setlists?skip=2&limit=5", headers=headers)
    assert response_skip.status_code == 200


@pytest.mark.asyncio
async def test_get_setlists_filter_by_type(client: AsyncClient, db):
    """Test filtering setlists by type (setlist or event)."""
    # Seed setlists data
    await client.post("/api/theater/setlists/seed")

    # Register and Login
    register_payload = {
        "fullName": "Filter User",
        "memberId": "33333",
        "username": "filteruser",
        "email": "filter@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "filteruser"},
        {"$set": {"isEmailVerified": True}}
    )

    login_res = await client.post("/api/auth/signin", data={
        "username": "filteruser",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Filter by type=setlist
    response = await client.get("/api/theater/setlists?type=setlist", headers=headers)
    assert response.status_code == 200
    data = response.json()
    for setlist in data["setlists"]:
        assert setlist["type"] == "setlist"

    # Filter by type=event
    response = await client.get("/api/theater/setlists?type=event", headers=headers)
    assert response.status_code == 200
    data = response.json()
    for setlist in data["setlists"]:
        assert setlist["type"] == "event"


@pytest.mark.asyncio
async def test_get_setlists_filter_by_active(client: AsyncClient, db):
    """Test filtering setlists by active status."""
    # Seed setlists data
    await client.post("/api/theater/setlists/seed")

    # Register and Login
    register_payload = {
        "fullName": "Active Filter User",
        "memberId": "44444",
        "username": "activefilteruser",
        "email": "activefilter@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "activefilteruser"},
        {"$set": {"isEmailVerified": True}}
    )

    login_res = await client.post("/api/auth/signin", data={
        "username": "activefilteruser",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Filter by active=true
    response = await client.get("/api/theater/setlists?active=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    for setlist in data["setlists"]:
        assert setlist["active"] is True

    # Filter by active=false
    response = await client.get("/api/theater/setlists?active=false", headers=headers)
    assert response.status_code == 200
    data = response.json()
    for setlist in data["setlists"]:
        assert setlist["active"] is False


@pytest.mark.asyncio
async def test_get_setlist_types(client: AsyncClient, db):
    """Test getting list of setlist types."""
    await client.post("/api/theater/setlists/seed")

    response = await client.get("/api/theater/setlists/types")
    assert response.status_code == 200
    types = response.json()
    assert isinstance(types, list)
    assert "setlist" in types
    assert "event" in types


@pytest.mark.asyncio
async def test_get_setlist_by_id(client: AsyncClient, db):
    """Test getting a setlist by its ID."""
    await client.post("/api/theater/setlists/seed")

    # Get a setlist from the list
    # First we need to authenticate to get the list
    register_payload = {
        "fullName": "ID User",
        "memberId": "55555",
        "username": "iduser",
        "email": "iduser@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "iduser"},
        {"$set": {"isEmailVerified": True}}
    )

    login_res = await client.post("/api/auth/signin", data={
        "username": "iduser",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get one setlist ID
    list_res = await client.get("/api/theater/setlists?limit=1", headers=headers)
    setlist = list_res.json()["setlists"][0]
    setlist_id = setlist["setlistId"]

    # Get by ID (this endpoint doesn't require auth)
    response = await client.get(f"/api/theater/setlists/id/{setlist_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["setlistId"] == setlist_id
    assert data["title"] == setlist["title"]


@pytest.mark.asyncio
async def test_get_setlist_by_id_not_found(client: AsyncClient, db):
    """Test getting a non-existent setlist by ID returns 404."""
    await client.post("/api/theater/setlists/seed")

    response = await client.get("/api/theater/setlists/id/non-existent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_setlist_by_title(client: AsyncClient, db):
    """Test getting a setlist by its title."""
    await client.post("/api/theater/setlists/seed")

    # Use a known title from the seed data
    response = await client.get("/api/theater/setlists/title/Pajama Drive")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Pajama Drive"
    assert data["type"] == "setlist"


@pytest.mark.asyncio
async def test_get_setlist_by_title_not_found(client: AsyncClient, db):
    """Test getting a non-existent setlist by title returns 404."""
    await client.post("/api/theater/setlists/seed")

    response = await client.get("/api/theater/setlists/title/Non Existent Setlist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_setlist_watched_stats_with_tickets(client: AsyncClient, db):
    """Test that watched stats are correctly calculated with user tickets."""
    # Seed setlists
    await client.post("/api/theater/setlists/seed")

    # Register and Login
    username = "watcheduser"
    register_payload = {
        "fullName": "Watched User",
        "memberId": "66666",
        "username": username,
        "email": "watched@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "watcheduser"},
        {"$set": {"isEmailVerified": True}}
    )

    user = await db["users"].find_one({"username": username})
    user_id = user["userId"]

    login_res = await client.post("/api/auth/signin", data={
        "username": "watcheduser",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Insert tickets for "Pajama Drive" (2 tickets)
    ticket_data_1 = TicketInDB(
        user_id=user_id,
        ticket_id="T001",
        event=TicketEvent(
            title="Pajama Drive",
            date="2023-01-15",
            day="Sunday",
            time="14:00",
            venue="JKT48 Theater"
        ),
        seat=TicketSeat(section="A", number=5),
        price=200000,
        currency="IDR",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    ticket_data_2 = TicketInDB(
        user_id=user_id,
        ticket_id="T002",
        event=TicketEvent(
            title="Pajama Drive",
            date="2023-02-20",
            day="Monday",
            time="19:00",
            venue="JKT48 Theater"
        ),
        seat=TicketSeat(section="B", number=10),
        price=200000,
        currency="IDR",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    # Insert 1 ticket for "Pertaruhan Cinta"
    ticket_data_3 = TicketInDB(
        user_id=user_id,
        ticket_id="T003",
        event=TicketEvent(
            title="Pertaruhan Cinta",
            date="2023-03-15",
            day="Wednesday",
            time="14:00",
            venue="JKT48 Theater"
        ),
        seat=TicketSeat(section="C", number=3),
        price=200000,
        currency="IDR",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    await db["tickets"].insert_many([
        ticket_data_1.model_dump(),
        ticket_data_2.model_dump(),
        ticket_data_3.model_dump()
    ])

    # Get setlists
    response = await client.get("/api/theater/setlists", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Find Pajama Drive and check stats
    pajama_drive = next(
        (s for s in data["setlists"] if s["title"] == "Pajama Drive"),
        None
    )
    assert pajama_drive is not None
    assert pajama_drive["watched"]["count"] == 2
    assert pajama_drive["watched"]["isMostWatched"] is True
    assert pajama_drive["watched"]["percentage"] == 100.0

    # Find Pertaruhan Cinta and check stats
    pertaruhan_cinta = next(
        (s for s in data["setlists"] if s["title"] == "Pertaruhan Cinta"),
        None
    )
    assert pertaruhan_cinta is not None
    assert pertaruhan_cinta["watched"]["count"] == 1
    assert pertaruhan_cinta["watched"]["isMostWatched"] is False


@pytest.mark.asyncio
async def test_setlist_max_attendance_in_response(client: AsyncClient, db):
    """Test that maxAttendance is correctly set in response."""
    # Seed setlists
    await client.post("/api/theater/setlists/seed")

    # Register and Login (no tickets - maxAttendance should be 0)
    register_payload = {
        "fullName": "Max User",
        "memberId": "77777",
        "username": "maxuser",
        "email": "max@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "maxuser"},
        {"$set": {"isEmailVerified": True}}
    )

    login_res = await client.post("/api/auth/signin", data={
        "username": "maxuser",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get setlists - user has no tickets, so maxAttendance should be 0
    response = await client.get("/api/theater/setlists", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["maxAttendance"] == 0

    # All watched counts should be 0
    for setlist in data["setlists"]:
        assert setlist["watched"]["count"] == 0
        assert setlist["watched"]["percentage"] == 0.0
        assert setlist["watched"]["isMostWatched"] is False
