import pytest
from httpx import AsyncClient
from datetime import datetime
from src.tickets.schemas import TicketInDB, TicketEvent, TicketSeat, TicketTwoShot


@pytest.mark.asyncio
async def test_get_memories_unauthorized(client: AsyncClient):
    response = await client.get("/api/memories")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_memories_empty(client: AsyncClient, db):
    # Register and Login
    register_payload = {
        "fullName": "Memory User",
        "memberId": "33333",
        "username": "memoryuser",
        "email": "memory@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "memoryuser"}, 
        {"$set": {"isEmailVerified": True}}
    )

    login_res = await client.post("/api/auth/signin", data={
        "username": "memoryuser",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get Memories (Empty - no tickets with images)
    response = await client.get("/api/memories", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["total_data"] == 0
    assert len(data["data"]) == 0


@pytest.mark.asyncio
async def test_get_memories_with_images(client: AsyncClient, db):
    # Register and Login
    username = "memoryuser2"
    register_payload = {
        "fullName": "Memory User 2",
        "memberId": "44444",
        "username": username,
        "email": "memory2@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": username}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    user = await db["users"].find_one({"username": username})
    user_id = user["userId"]

    login_res = await client.post("/api/auth/signin", data={
        "username": username,
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Insert ticket WITH image
    ticket_data = TicketInDB(
        user_id=user_id,
        ticket_id="M123",
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
        imageUrl="data:image/png;base64,iVBORw0KGgo=",  # Sample base64 image
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    await db["tickets"].insert_one(ticket_data.model_dump())

    # Get Memories
    response = await client.get("/api/memories", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["meta"]["total_data"] == 1
    assert len(data["data"]) == 1
    assert data["data"][0]["type"] == "TICKET"
    assert "Pajama Drive" in data["data"][0]["title"]


@pytest.mark.asyncio
async def test_get_memories_with_2shot(client: AsyncClient, db):
    # Register and Login
    username = "memoryuser3"
    register_payload = {
        "fullName": "Memory User 3",
        "memberId": "55555",
        "username": username,
        "email": "memory3@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": username}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    user = await db["users"].find_one({"username": username})
    user_id = user["userId"]

    login_res = await client.post("/api/auth/signin", data={
        "username": username,
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Insert ticket with both ticket image and 2-shot image
    ticket_data = TicketInDB(
        user_id=user_id,
        ticket_id="M456",
        event=TicketEvent(
            title="Aitakatta",
            date="2023-02-20",
            day="Monday",
            time="19:00",
            venue="JKT48 Theater"
        ),
        seat=TicketSeat(section="B", number=10),
        price=200000,
        currency="IDR",
        imageUrl="data:image/png;base64,iVBORw0KGgo=",
        two_shot=TicketTwoShot(
            member_name="Freya Jayawardana",
            type="Roulette",
            price=50000,
            imageUrl="data:image/png;base64,iVBORw0KGgo="
        ),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    await db["tickets"].insert_one(ticket_data.model_dump())

    # Get All Memories (should return 2 items: 1 ticket + 1 2shot)
    response = await client.get("/api/memories", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["meta"]["total_data"] == 2
    assert len(data["data"]) == 2
    types = [item["type"] for item in data["data"]]
    assert "TICKET" in types
    assert "2SHOT" in types

    # Filter by TICKET
    response = await client.get("/api/memories?type=TICKET", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_data"] == 1
    assert data["data"][0]["type"] == "TICKET"

    # Filter by 2SHOT
    response = await client.get("/api/memories?type=2SHOT", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_data"] == 1
    assert data["data"][0]["type"] == "2SHOT"
    assert "Freya" in data["data"][0]["twoShotMemberName"]
