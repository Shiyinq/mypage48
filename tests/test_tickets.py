import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_ticket_success(client: AsyncClient, db, create_user):
    """Test creating a ticket."""
    token, user_id, headers = await create_user("theateruser")

    # Create Ticket
    ticket_payload = {
        "ticket_id": "T-12345",
        "event": {
            "title": "Renai Kinshi Jourei",
            "date": "2024-01-01",
            "day": "Monday",
            "time": "19:00",
            "gate_open": "18:30"
        },
        "seat": {
            "section": "A",
            "number": "1"
        },
        "price": 200000,
        "currency": "IDR",
        "rules": {},
        "notes": "Test ticket"
    }
    
    response = await client.post("/api/theater/tickets", json=ticket_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["event"]["title"] == "Renai Kinshi Jourei"
    assert data["ticket_id"] == "T-12345"
    assert "_id" in data

@pytest.mark.asyncio
async def test_get_tickets(client: AsyncClient, db, create_user):
    """Test getting user's tickets."""
    token, user_id, headers = await create_user("ticketsuser")

    ticket_payload = {
        "ticket_id": "T-67890",
        "event": {
            "title": "Ramune",
            "date": "2024-01-02",
            "day": "Tuesday",
            "time": "19:00",
            "gate_open": "18:30"
        },
        "seat": {
            "section": "B",
            "number": "2"
        },
        "price": 200000
    }
    await client.post("/api/theater/tickets", json=ticket_payload, headers=headers)

    # Get Tickets
    response = await client.get("/api/theater/tickets", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1
    assert data["data"][0]["event"]["title"] == "Ramune"

@pytest.mark.asyncio
async def test_update_ticket(client: AsyncClient, db, create_user):
    """Test updating a ticket."""
    token, user_id, headers = await create_user("updateticket")

    # Create
    create_payload = {
        "ticket_id": "T-UDP",
        "event": {
            "title": "Original Show",
            "date": "2024-01-03",
            "day": "Wednesday",
            "time": "19:00",
            "gate_open": "18:30"
        },
        "seat": {
            "section": "C",
            "number": "3"
        },
        "price": 200000
    }
    create_res = await client.post("/api/theater/tickets", json=create_payload, headers=headers)
    ticket_data = create_res.json()
    ticket_id = ticket_data["_id"]

    # Update
    update_data = {
        "event": {
            "title": "Updated Show",
            "date": "2024-01-03",
            "day": "Wednesday",
            "time": "19:00"
        },
        "seat": {
            "section": "D",
            "number": "4"
        }
    }
    response = await client.put(f"/api/theater/tickets/{ticket_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["event"]["title"] == "Updated Show"
    assert data["seat"]["section"] == "D"
    assert data["seat"]["number"] == "4"

@pytest.mark.asyncio
async def test_delete_ticket(client: AsyncClient, db, create_user):
    """Test deleting a ticket."""
    token, user_id, headers = await create_user("delticket")

    # Create
    create_payload = {
        "ticket_id": "T-DEL",
        "event": {
            "title": "To Delete",
            "date": "2024-01-04",
            "day": "Thursday",
            "time": "19:00",
            "gate_open": "18:30"
        },
        "seat": {
            "section": "E",
            "number": "5"
        },
        "price": 200000
    }
    create_res = await client.post("/api/theater/tickets", json=create_payload, headers=headers)
    ticket_data = create_res.json()
    ticket_id = ticket_data["_id"]

    # Delete
    response = await client.delete(f"/api/theater/tickets/{ticket_id}", headers=headers)
    assert response.status_code == 200
    
    # Verify deletion.
    get_res = await client.get(f"/api/theater/tickets/{ticket_id}", headers=headers)
    assert get_res.status_code == 404

@pytest.mark.asyncio
async def test_ticket_image_validation(client: AsyncClient, db, create_user):
    """Test validation of ticket and two-shot image paths/lengths."""
    token, user_id, headers = await create_user("ticketval")

    # 1. Invalid ticket image prefix
    payload = {
        "ticket_id": "T-ERR",
        "event": {"title": "Test", "date": "2024-01-01", "day": "Mon", "time": "19:00"},
        "seat": {"section": "A", "number": 1},
        "price": 1,
        "imageUrl": "wrong/prefix.jpg"
    }
    res = await client.post("/api/theater/tickets", json=payload, headers=headers)
    assert res.status_code == 422
    assert "Ticket image path must start with 'ticket/'" in res.text

    # 2. Invalid two-shot image prefix
    payload["imageUrl"] = "ticket/ok.jpg"
    payload["two_shot"] = {
        "member_name": "Feni",
        "price": 50000,
        "imageUrl": "wrong/two.jpg"
    }
    res = await client.post("/api/theater/tickets", json=payload, headers=headers)
    assert res.status_code == 422
    assert "Two-shot image path must start with 'twoshot/'" in res.text

    # 3. Test max length
    payload["imageUrl"] = "ticket/" + "a" * 100
    res = await client.post("/api/theater/tickets", json=payload, headers=headers)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_get_tickets_invalid_date(client: AsyncClient, create_user):
    """Test getting tickets with invalid date format."""
    token, user_id, headers = await create_user("ticketsuser_invalid")

    response = await client.get("/api/theater/tickets?end_date=invalid-date", headers=headers)
    assert response.status_code == 400
    assert "INVALID_DATE_FORMAT" in response.text


@pytest.mark.asyncio
async def test_create_ticket_default_favorite(client: AsyncClient, db, create_user):
    """Test that a new ticket has is_favorite set to false by default."""
    token, user_id, headers = await create_user("favdefault")

    payload = {
        "ticket_id": "T-FAV0",
        "event": {"title": "Test Show", "date": "2024-05-01", "day": "Wednesday", "time": "19:00"},
        "seat": {"section": "A", "number": "1"},
        "price": 100000,
    }
    response = await client.post("/api/theater/tickets", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["is_favorite"] is False


@pytest.mark.asyncio
async def test_toggle_favorite(client: AsyncClient, db, create_user):
    """Test toggling the favorite status of a ticket."""
    token, user_id, headers = await create_user("favtoggle")

    # Create a ticket
    payload = {
        "ticket_id": "T-FAV1",
        "event": {"title": "Fav Test", "date": "2024-06-01", "day": "Saturday", "time": "18:00"},
        "seat": {"section": "B", "number": "2"},
        "price": 150000,
    }
    create_res = await client.post("/api/theater/tickets", json=payload, headers=headers)
    ticket_data = create_res.json()
    ticket_id = ticket_data["_id"]

    # Toggle to favorite (false -> true)
    response = await client.patch(f"/api/theater/tickets/{ticket_id}/favorite", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_favorite"] is True

    # Toggle again (true -> false)
    response = await client.patch(f"/api/theater/tickets/{ticket_id}/favorite", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_favorite"] is False


@pytest.mark.asyncio
async def test_toggle_favorite_nonexistent_ticket(client: AsyncClient, db, create_user):
    """Test toggling favorite on a non-existent ticket returns 404."""
    token, user_id, headers = await create_user("favnonexist")
    fake_id = "000000000000000000000000"

    response = await client.patch(f"/api/theater/tickets/{fake_id}/favorite", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_filter_favorite_tickets(client: AsyncClient, db, create_user):
    """Test filtering tickets by is_favorite flag."""
    token, user_id, headers = await create_user("favfilter")

    # Create two tickets
    payload1 = {
        "ticket_id": "T-FAV2",
        "event": {"title": "Show A", "date": "2024-07-01", "day": "Monday", "time": "19:00"},
        "seat": {"section": "C", "number": "1"},
        "price": 100000,
    }
    res1 = await client.post("/api/theater/tickets", json=payload1, headers=headers)
    id1 = res1.json()["_id"]

    payload2 = {
        "ticket_id": "T-FAV3",
        "event": {"title": "Show B", "date": "2024-07-02", "day": "Tuesday", "time": "19:00"},
        "seat": {"section": "C", "number": "2"},
        "price": 100000,
    }
    res2 = await client.post("/api/theater/tickets", json=payload2, headers=headers)
    id2 = res2.json()["_id"]

    # Favorite the first ticket
    await client.patch(f"/api/theater/tickets/{id1}/favorite", headers=headers)

    # Filter by is_favorite=true
    response = await client.get("/api/theater/tickets?is_favorite=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["_id"] == id1
    assert data["data"][0]["is_favorite"] is True

    # Filter by is_favorite=false should return tickets where is_favorite is false
    # (really this would include tickets without the field, but we just check
    #  that no favorited tickets appear)
    response = await client.get("/api/theater/tickets?is_favorite=false", headers=headers)
    assert response.status_code == 200
    data = response.json()
    for t in data["data"]:
        assert t.get("is_favorite") is not True


@pytest.mark.asyncio
async def test_create_ticket_default_two_shot_favorite(client: AsyncClient, db, create_user):
    """Test that a new ticket with two_shot has is_favorite set to false by default."""
    token, user_id, headers = await create_user("tsfavdef")

    payload = {
        "ticket_id": "T-2FAV0",
        "event": {"title": "2Shot Test", "date": "2024-08-01", "day": "Thursday", "time": "19:00"},
        "seat": {"section": "A", "number": "1"},
        "price": 100000,
        "two_shot": {
            "member_name": "Feni",
            "price": 50000,
            "imageUrl": "twoshot/test.jpg",
        },
    }
    response = await client.post("/api/theater/tickets", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["two_shot"]["is_favorite"] is False


@pytest.mark.asyncio
async def test_toggle_two_shot_favorite(client: AsyncClient, db, create_user):
    """Test toggling the favorite status of a two-shot."""
    token, user_id, headers = await create_user("tsfavtoggle")

    payload = {
        "ticket_id": "T-2FAV1",
        "event": {"title": "2Shot Fav", "date": "2024-08-15", "day": "Thursday", "time": "18:00"},
        "seat": {"section": "B", "number": "2"},
        "price": 150000,
        "two_shot": {
            "member_name": "Feni",
            "price": 50000,
            "imageUrl": "twoshot/test.jpg",
        },
    }
    create_res = await client.post("/api/theater/tickets", json=payload, headers=headers)
    ticket_data = create_res.json()
    ticket_id = ticket_data["_id"]

    # Toggle to favorite (false -> true)
    response = await client.patch(f"/api/theater/tickets/{ticket_id}/two-shot/favorite", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["two_shot"]["is_favorite"] is True

    # Toggle again (true -> false)
    response = await client.patch(f"/api/theater/tickets/{ticket_id}/two-shot/favorite", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["two_shot"]["is_favorite"] is False


@pytest.mark.asyncio
async def test_toggle_two_shot_favorite_nonexistent_ticket(client: AsyncClient, db, create_user):
    """Test toggling two-shot favorite on a non-existent ticket returns 404."""
    token, user_id, headers = await create_user("tsfavnonexist")
    fake_id = "000000000000000000000000"

    response = await client.patch(f"/api/theater/tickets/{fake_id}/two-shot/favorite", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_toggle_two_shot_favorite_no_two_shot(client: AsyncClient, db, create_user):
    """Test toggling two-shot favorite on a ticket without two_shot returns 404."""
    token, user_id, headers = await create_user("tsfavnotwo")

    payload = {
        "ticket_id": "T-2FAVX",
        "event": {"title": "No 2Shot", "date": "2024-09-01", "day": "Sunday", "time": "19:00"},
        "seat": {"section": "A", "number": "1"},
        "price": 100000,
    }
    create_res = await client.post("/api/theater/tickets", json=payload, headers=headers)
    ticket_id = create_res.json()["_id"]

    response = await client.patch(f"/api/theater/tickets/{ticket_id}/two-shot/favorite", headers=headers)
    assert response.status_code == 404
