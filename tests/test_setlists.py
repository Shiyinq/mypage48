import pytest
from httpx import AsyncClient
from datetime import datetime
from src.tickets.schemas import TicketInDB, TicketEvent, TicketSeat

# Minimal test data
# Minimal test data
TEST_SETLISTS_DATA = [
    {
        "setlistId": "pajamadrive",
        "title": "Pajama Drive",
        "titleJapanese": "Pajama Drive",
        "description": "A classic setlist.",
        "type": "setlist",
        "imageUrl": "https://example.com/pajama.jpg",
        "active": True,
        "songs": ["Shonichi"],
        "id": "1",
        "songDetails": [
             {
                 "id": "1",
                 "title": "Shonichi",
                 "lyric": "Impian ada di tengah peluh..."
             }
        ]
    },
    {
        "setlistId": "pertaruhancinta",
        "title": "Pertaruhan Cinta",
        "titleJapanese": "Renai Kinshi Jourei",
        "description": "Love Forbidden Ordinance",
        "type": "setlist",
        "imageUrl": "https://example.com/rkj.jpg",
        "active": True,
        "songs": [],
        "id": "2"
    },
    {
        "setlistId": "specialevent",
        "title": "Special Event",
        "titleJapanese": "Special Event",
        "description": "Special event.",
        "type": "event",
        "imageUrl": "https://example.com/event.jpg",
        "active": False,
        "songs": [],
        "id": "3"
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
async def test_get_setlists_list(client: AsyncClient, db, seed_setlists_db, create_user):
    """Test getting all setlists with authentication."""
    token, user_id, headers = await create_user("setlistuser")

    # Get setlists
    response = await client.get("/api/theater/setlists", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert data["total"] > 0
    assert len(data["setlists"]) > 0

@pytest.mark.asyncio
async def test_get_setlists_pagination(client: AsyncClient, db, seed_setlists_db, create_user):
    """Test setlists pagination."""
    token, user_id, headers = await create_user("paginationuser")

    # Test limit parameter
    response = await client.get("/api/theater/setlists?limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["setlists"]) <= 2

@pytest.mark.asyncio
async def test_get_setlists_filter_by_type(client: AsyncClient, db, seed_setlists_db, create_user):
    """Test filtering setlists by type (setlist or event)."""
    token, user_id, headers = await create_user("filteruser")

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
async def test_get_setlists_filter_by_active(client: AsyncClient, db, seed_setlists_db, create_user):
    """Test filtering setlists by active status."""
    token, user_id, headers = await create_user("activefilter")

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
async def test_get_setlist_types(client: AsyncClient, seed_setlists_db, create_user):
    """Test getting list of setlist types."""
    token, user_id, headers = await create_user("typesuser")
    
    response = await client.get("/api/theater/setlists/types", headers=headers)
    assert response.status_code == 200
    types = response.json()
    assert isinstance(types, list)
    assert "setlist" in types
    assert "event" in types

@pytest.mark.asyncio
async def test_get_setlist_by_id(client: AsyncClient, seed_setlists_db, create_user):
    """Test getting a setlist by its ID."""
    token, user_id, headers = await create_user("iduser")

    setlist_id = "pajamadrive" # Pajama Drive
    response = await client.get(f"/api/theater/setlists/id/{setlist_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["setlistId"] == setlist_id
    assert data["title"] == "Pajama Drive"

@pytest.mark.asyncio
async def test_get_setlist_by_id_not_found(client: AsyncClient, create_user):
    """Test getting a non-existent setlist by ID returns 404."""
    token, user_id, headers = await create_user("notfounduser")

    response = await client.get("/api/theater/setlists/id/non-existent-id", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_setlist_by_title(client: AsyncClient, seed_setlists_db, create_user):
    """Test getting a setlist by its title."""
    token, user_id, headers = await create_user("titleuser")

    response = await client.get("/api/theater/setlists/title/Pajama Drive", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Pajama Drive"
    assert data["type"] == "setlist"

@pytest.mark.asyncio
async def test_get_setlist_by_title_not_found(client: AsyncClient, create_user):
    """Test getting a non-existent setlist by title returns 404."""
    token, user_id, headers = await create_user("titlenotfounduser")

    response = await client.get("/api/theater/setlists/title/Non Existent Setlist", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_setlist_watched_stats_with_tickets(client: AsyncClient, db, seed_setlists_db, create_user):
    """Test that watched stats are correctly calculated with user tickets."""
    token, user_id, headers = await create_user("watcheduser")

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
async def test_delete_setlist(client: AsyncClient, db, seed_setlists_db, create_user):
    """Test deleting a setlist (admin only)."""
    token, user_id, headers = await create_user("adminsetlist", is_admin=True)

    setlist_id = "pajamadrive"
    response = await client.delete(f"/api/theater/setlists/{setlist_id}", headers=headers)
    assert response.status_code == 200
    # Check for standardized message
    assert response.json()["message"] == "Setlist deleted successfully."

    # Verify deleted
    get_res = await client.get(f"/api/theater/setlists/id/{setlist_id}", headers=headers)
    assert get_res.status_code == 404

@pytest.mark.asyncio
async def test_create_setlist_forbidden(client: AsyncClient, db, create_user):
    """Test that non-admin users cannot create a setlist."""
    token, user_id, headers = await create_user("normscreate")

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
async def test_update_setlist_forbidden(client: AsyncClient, db, create_user):
    """Test that non-admin users cannot update a setlist."""
    token, user_id, headers = await create_user("normsupdate")

    setlist_id = "pajamadrive"
    payload = {"title": "Updated Title"}
    response = await client.put(f"/api/theater/setlists/{setlist_id}", json=payload, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_setlist_forbidden(client: AsyncClient, db, create_user):
    """Test that non-admin users cannot delete a setlist."""
    token, user_id, headers = await create_user("normsdelete")

    setlist_id = "pajamadrive"
    response = await client.delete(f"/api/theater/setlists/{setlist_id}", headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_setlist_validation(client: AsyncClient, db, create_user):
    """Test validation of setlist imageUrl, title, type, and description."""
    token, user_id, headers = await create_user("setlistval", is_admin=True)

    # 1. Invalid image prefix
    payload = {
        "title": "New",
        "description": "Desc",
        "type": "setlist",
        "imageUrl": "wrong/prefix.jpg"
    }
    res = await client.post("/api/theater/setlists", json=payload, headers=headers)
    assert res.status_code == 422
    assert "Setlist image path must start with 'media/setlists/'" in res.text

    # 2. Invalid type
    payload["imageUrl"] = "media/setlists/ok.jpg"
    payload["type"] = "concert" # only 'setlist' or 'event' allowed
    res = await client.post("/api/theater/setlists", json=payload, headers=headers)
    assert res.status_code == 422

    # 3. Test max length for title
    payload["type"] = "setlist"
    payload["title"] = "a" * 101
    res = await client.post("/api/theater/setlists", json=payload, headers=headers)
    assert res.status_code == 422
