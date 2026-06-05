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
