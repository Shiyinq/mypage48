import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_concert_admin(client: AsyncClient, create_user):
    # Create an admin user
    _, _, admin_headers = await create_user(
        username="adminuser", is_admin=True
    )

    concert_data = {
        "title": "Test Concert 2026",
        "theme": "The Testing Era",
        "type": "Anniversary",
        "date": "2026-12-17T00:00:00Z",
        "location": "Gelora Bung Karno",
        "details": "A test concert for pytest.",
        "benefits": ["Free Merch", "Meet & Greet"],
        "ticket_price": ["VIP: Rp 1.000.000"],
        "image": "http://example.com/poster.jpg"
    }

    res = await client.post("/api/theater/concerts/", json=concert_data, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == concert_data["title"]
    assert "id" in data


@pytest.mark.asyncio
async def test_create_concert_unauthorized(client: AsyncClient, create_user):
    # Create a normal user
    _, _, user_headers = await create_user(username="normaluser")

    concert_data = {
        "title": "Unauthorized Concert",
        "theme": "-",
        "type": "Live",
        "date": "2026-12-17T00:00:00Z",
        "location": "Theater",
        "details": "Details",
        "benefits": [],
        "ticket_price": [],
        "image": ""
    }

    res = await client.post("/api/theater/concerts/", json=concert_data, headers=user_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_get_all_concerts(client: AsyncClient, create_user):
    _, _, admin_headers = await create_user(
        username="adminuser2", is_admin=True
    )
    # Insert 2 concerts
    await client.post("/api/theater/concerts/", json={
        "title": "Concert A",
        "theme": "-",
        "type": "Live",
        "date": "2026-12-17T00:00:00Z",
        "location": "Loc A",
        "details": "Det A",
        "benefits": [],
        "ticket_price": [],
        "image": ""
    }, headers=admin_headers)
    await client.post("/api/theater/concerts/", json={
        "title": "Concert B",
        "theme": "-",
        "type": "Live",
        "date": "2027-12-17T00:00:00Z",
        "location": "Loc B",
        "details": "Det B",
        "benefits": [],
        "ticket_price": [],
        "image": ""
    }, headers=admin_headers)

    res = await client.get("/api/theater/concerts/")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_concert_by_id(client: AsyncClient, create_user):
    _, _, admin_headers = await create_user(
        username="adminuser3", is_admin=True
    )
    create_res = await client.post("/api/theater/concerts/", json={
        "title": "Target Concert",
        "theme": "-",
        "type": "Live",
        "date": "2026-12-17T00:00:00Z",
        "location": "Loc",
        "details": "Det",
        "benefits": [],
        "ticket_price": [],
        "image": ""
    }, headers=admin_headers)
    concert_id = create_res.json()["id"]

    res = await client.get(f"/api/theater/concerts/{concert_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == concert_id
    assert data["title"] == "Target Concert"


@pytest.mark.asyncio
async def test_update_concert(client: AsyncClient, create_user):
    _, _, admin_headers = await create_user(
        username="adminuser4", is_admin=True
    )
    create_res = await client.post("/api/theater/concerts/", json={
        "title": "Old Title",
        "theme": "-",
        "type": "Live",
        "date": "2026-12-17T00:00:00Z",
        "location": "Loc",
        "details": "Det",
        "benefits": [],
        "ticket_price": [],
        "image": ""
    }, headers=admin_headers)
    concert_id = create_res.json()["id"]

    update_payload = {
        "title": "New Title",
        "theme": "New Theme",
        "type": "Live",
        "date": "2026-12-17T00:00:00Z",
        "location": "Loc",
        "details": "Det",
        "benefits": [],
        "ticket_price": [],
        "image": ""
    }
    update_res = await client.put(f"/api/theater/concerts/{concert_id}", json=update_payload, headers=admin_headers)
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["title"] == "New Title"
    assert data["theme"] == "New Theme"


@pytest.mark.asyncio
async def test_delete_concert(client: AsyncClient, create_user):
    _, _, admin_headers = await create_user(
        username="adminuser5", is_admin=True
    )
    create_res = await client.post("/api/theater/concerts/", json={
        "title": "To Delete",
        "theme": "-",
        "type": "Live",
        "date": "2026-12-17T00:00:00Z",
        "location": "Loc",
        "details": "Det",
        "benefits": [],
        "ticket_price": [],
        "image": ""
    }, headers=admin_headers)
    concert_id = create_res.json()["id"]

    delete_res = await client.delete(f"/api/theater/concerts/{concert_id}", headers=admin_headers)
    assert delete_res.status_code == 200

    # Ensure it's deleted
    get_res = await client.get(f"/api/theater/concerts/{concert_id}")
    assert get_res.status_code == 404
