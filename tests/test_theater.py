import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_ticket_success(client: AsyncClient, db):
    # Register and Login
    register_payload = {
        "fullName": "Theater User",
        "memberId": "theater123",
        "username": "theateruser",
        "email": "theater@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    await db["users"].update_one(
        {"username": "theateruser"}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    login_res = await client.post("/api/auth/signin", data={"username": "theateruser", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Ticket
    # Correct structure based on Schema
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
async def test_get_tickets(client: AsyncClient, db):
    # Setup user and ticket
    register_payload = {
        "fullName": "Tickets User",
        "memberId": "tickets123",
        "username": "ticketsuser",
        "email": "tickets@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    await db["users"].update_one(
        {"username": "ticketsuser"}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    login_res = await client.post("/api/auth/signin", data={"username": "ticketsuser", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

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
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["event"]["title"] == "Ramune"

@pytest.mark.asyncio
async def test_update_ticket(client: AsyncClient, db):
    # Setup user
    register_payload = {
        "fullName": "Update User",
        "memberId": "upd123",
        "username": "updateticket",
        "email": "updateticket@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    await db["users"].update_one(
        {"username": "updateticket"}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    login_res = await client.post("/api/auth/signin", data={"username": "updateticket", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

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
async def test_delete_ticket(client: AsyncClient, db):
    # Setup user
    register_payload = {
        "fullName": "Del User",
        "memberId": "del123",
        "username": "delticket",
        "email": "delticket@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    await db["users"].update_one(
        {"username": "delticket"}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    login_res = await client.post("/api/auth/signin", data={"username": "delticket", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

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
    # The route returns TicketResponse. If service raises TicketNotFound -> 404.
    assert get_res.status_code == 404
