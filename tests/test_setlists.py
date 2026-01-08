import pytest
from httpx import AsyncClient
from datetime import datetime
from src.tickets.schemas import TicketInDB, TicketEvent, TicketSeat

# Minimal test data
TEST_SETLISTS_DATA = [
    {
        "setlistId": "S001",
        "title": "Pajama Drive",
        "titleJapanese": "Pajama Drive",
        "description": "A classic setlist.",
        "type": "setlist",
        "imageUrl": "https://example.com/pajama.jpg",
        "active": True,
        "songs": []
    },
    {
        "setlistId": "S002",
        "title": "Pertaruhan Cinta",
        "titleJapanese": "Renai Kinshi Jourei",
        "description": "Love Forbidden Ordinance",
        "type": "setlist",
        "imageUrl": "https://example.com/rkj.jpg",
        "active": True,
        "songs": []
    },
    {
        "setlistId": "E001",
        "title": "Special Event",
        "titleJapanese": "Special Event",
        "description": "Special event.",
        "type": "event",
        "imageUrl": "https://example.com/event.jpg",
        "active": False,
        "songs": []
    }
]

@pytest.fixture
async def seed_setlists_db(db):
    """Seed the database with local test setlist data."""
    if TEST_SETLISTS_DATA:
        await db["setlists"].insert_many(TEST_SETLISTS_DATA)

@pytest.mark.asyncio
async def test_get_setlists_unauthorized(client: AsyncClient):
    """Test that unauthorized users cannot access setlists endpoint."""
    response = await client.get("/api/theater/setlists")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_setlists_list(client: AsyncClient, db, seed_setlists_db):
    """Test getting all setlists with authentication."""
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
    assert data["total"] > 0
    assert len(data["setlists"]) > 0

@pytest.mark.asyncio
async def test_get_setlists_pagination(client: AsyncClient, db, seed_setlists_db):
    """Test setlists pagination."""
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
    response = await client.get("/api/theater/setlists?limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["setlists"]) <= 2

@pytest.mark.asyncio
async def test_get_setlists_filter_by_type(client: AsyncClient, db, seed_setlists_db):
    """Test filtering setlists by type (setlist or event)."""
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
async def test_get_setlists_filter_by_active(client: AsyncClient, db, seed_setlists_db):
    """Test filtering setlists by active status."""
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
async def test_get_setlist_types(client: AsyncClient, seed_setlists_db):
    """Test getting list of setlist types."""
    response = await client.get("/api/theater/setlists/types")
    assert response.status_code == 200
    types = response.json()
    assert isinstance(types, list)
    assert "setlist" in types
    assert "event" in types

@pytest.mark.asyncio
async def test_get_setlist_by_id(client: AsyncClient, seed_setlists_db):
    """Test getting a setlist by its ID."""
    setlist_id = "S001" # Pajama Drive
    response = await client.get(f"/api/theater/setlists/id/{setlist_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["setlistId"] == setlist_id
    assert data["title"] == "Pajama Drive"

@pytest.mark.asyncio
async def test_get_setlist_by_id_not_found(client: AsyncClient):
    """Test getting a non-existent setlist by ID returns 404."""
    response = await client.get("/api/theater/setlists/id/non-existent-id")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_setlist_by_title(client: AsyncClient, seed_setlists_db):
    """Test getting a setlist by its title."""
    response = await client.get("/api/theater/setlists/title/Pajama Drive")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Pajama Drive"
    assert data["type"] == "setlist"

@pytest.mark.asyncio
async def test_get_setlist_by_title_not_found(client: AsyncClient):
    """Test getting a non-existent setlist by title returns 404."""
    response = await client.get("/api/theater/setlists/title/Non Existent Setlist")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_setlist_watched_stats_with_tickets(client: AsyncClient, db, seed_setlists_db):
    """Test that watched stats are correctly calculated with user tickets."""
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

    # Insert tickets matches TEST_SETLISTS_DATA titles
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
    
    await db["tickets"].insert_many([
        ticket_data_1.model_dump()
    ])

    # Get setlists
    response = await client.get("/api/theater/setlists", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Find Pajama Drive
    pajama_drive = next(
        (s for s in data["setlists"] if s["title"] == "Pajama Drive"),
        None
    )
    assert pajama_drive is not None
    assert pajama_drive["watched"]["count"] == 1

@pytest.mark.asyncio
async def test_delete_setlist(client: AsyncClient, db, seed_setlists_db):
    """Test deleting a setlist (admin only)."""
    # Admin Login
    await db["users"].insert_one({
        "fullName": "Admin User",
        "memberId": "99999",
        "username": "adminuser",
        "email": "admin@example.com",
        "hashedPassword": "hashedpassword", 
        "isEmailVerified": True,
        "role": "admin"
    })
    register_payload = {
        "fullName": "Admin Setlist",
        "memberId": "12345",
        "username": "adminsetlist",
        "email": "adminsetlist@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "adminsetlist"},
        {"$set": {"isEmailVerified": True, "isAdmin": True}}
    )
    login_res = await client.post("/api/auth/signin", data={
        "username": "adminsetlist",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    setlist_id = "S001"
    response = await client.delete(f"/api/theater/setlists/{setlist_id}", headers=headers)
    assert response.status_code == 200
    # Check for standardized message
    assert response.json()["message"] == "Setlist deleted successfully."

    # Verify deleted
    get_res = await client.get(f"/api/theater/setlists/id/{setlist_id}")
    assert get_res.status_code == 404

@pytest.mark.asyncio
async def test_create_setlist_forbidden(client: AsyncClient, db):
    """Test that non-admin users cannot create a setlist."""
    # Register Normal User
    register_payload = {
        "fullName": "Normal User SCreate",
        "memberId": "normscreate",
        "username": "normscreate",
        "email": "normscreate@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "normscreate"},
        {"$set": {"isEmailVerified": True}}
    )
    login_res = await client.post("/api/auth/signin", data={
        "username": "normscreate",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "setlistId": "NEW001",
        "title": "New Setlist",
        "titleJapanese": "New",
        "description": "Desc",
        "type": "setlist",
        "imageUrl": "https://example.com/new.jpg",
        "active": True
    }
    response = await client.post("/api/theater/setlists", json=payload, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_setlist_forbidden(client: AsyncClient, db):
    """Test that non-admin users cannot update a setlist."""
    # Register Normal User
    register_payload = {
        "fullName": "Normal User SUpdate",
        "memberId": "normsupdate",
        "username": "normsupdate",
        "email": "normsupdate@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "normsupdate"},
        {"$set": {"isEmailVerified": True}}
    )
    login_res = await client.post("/api/auth/signin", data={
        "username": "normsupdate",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    setlist_id = "S001"
    payload = {"title": "Updated Title"}
    response = await client.put(f"/api/theater/setlists/{setlist_id}", json=payload, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_setlist_forbidden(client: AsyncClient, db):
    """Test that non-admin users cannot delete a setlist."""
    # Register Normal User
    register_payload = {
        "fullName": "Normal User SDelete",
        "memberId": "normsdelete",
        "username": "normsdelete",
        "email": "normsdelete@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "normsdelete"},
        {"$set": {"isEmailVerified": True}}
    )
    login_res = await client.post("/api/auth/signin", data={
        "username": "normsdelete",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    setlist_id = "S001"
    response = await client.delete(f"/api/theater/setlists/{setlist_id}", headers=headers)
    assert response.status_code == 403
