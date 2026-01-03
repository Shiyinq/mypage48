import pytest
from httpx import AsyncClient
from datetime import datetime
from src.theater.schemas import TicketInDB, TicketEvent, TicketSeat

@pytest.mark.asyncio
async def test_get_achievements_unauthorized(client: AsyncClient):
    response = await client.get("/api/achievements")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_achievements_success_empty(client: AsyncClient, db):
    # 1. Register and Login
    register_payload = {
        "fullName": "Achievement User",
        "memberId": "11111",
        "username": "achievementuser",
        "email": "achieve@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    # Verify email manual
    await db["users"].update_one(
        {"username": "achievementuser"}, 
        {"$set": {"isEmailVerified": True}}
    )

    login_data = {
        "username": "achievementuser",
        "password": "Password123!"
    }
    login_res = await client.post("/api/auth/signin", data=login_data)
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Achievements (Empty)
    response = await client.get("/api/achievements", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "achievements" in data
    assert "unlockedCount" in data
    assert "totalCount" in data
    
    # Should be 0 unlocked
    assert data["unlockedCount"] == 0
    assert len(data["achievements"]) == data["totalCount"]
    
    # Verify specific locked achievement
    first_step = next((a for a in data["achievements"] if a["id"] == "first_show"), None)
    assert first_step is not None
    assert first_step["isUnlocked"] is False

@pytest.mark.asyncio
async def test_get_achievements_unlock_first_show(client: AsyncClient, db):
    # 1. Register and Login (New User)
    username = "achievementuser2"
    register_payload = {
        "fullName": "Achievement User 2",
        "memberId": "22222",
        "username": username,
        "email": "achieve2@example.com",
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

    login_data = {
        "username": username,
        "password": "Password123!"
    }
    login_res = await client.post("/api/auth/signin", data=login_data)
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Insert 1 Ticket directly to DB to simulate attendance
    ticket_data = TicketInDB(
        user_id=user_id,
        ticket_id="T123",
        event=TicketEvent(
            title="Pajama Drive",
            date="2023-01-01",
            day="Sunday",
            time="14:00",
            venue="JKT48 Theater"
        ),
        seat=TicketSeat(section="C", number=10),
        price=200000,
        currency="IDR",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    # Using model_dump() to convert to dict for MongoDB
    await db["tickets"].insert_one(ticket_data.model_dump())

    # 3. Get Achievements
    response = await client.get("/api/achievements", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Should have at least 1 unlocked (First Step)
    assert data["unlockedCount"] >= 1
    
    first_step = next((a for a in data["achievements"] if a["id"] == "first_show"), None)
    assert first_step is not None
    assert first_step["isUnlocked"] is True
