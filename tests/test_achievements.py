import pytest
from httpx import AsyncClient
from datetime import datetime
from src.tickets.schemas import TicketInDB, TicketEvent, TicketSeat

@pytest.mark.asyncio
async def test_get_achievements_unauthorized(client: AsyncClient):
    response = await client.get("/api/achievements")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_achievements_success_empty(client: AsyncClient, db, create_user):
    """Test getting achievements with no tickets."""
    token, user_id, headers = await create_user("achieveuser")

    # Get Achievements (Empty)
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
async def test_get_achievements_unlock_first_show(client: AsyncClient, db, create_user):
    """Test unlocking the first_show achievement."""
    token, user_id, headers = await create_user("achieveuser2")

    # Insert 1 Ticket directly to DB to simulate attendance
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
    await db["tickets"].insert_one(ticket_data.model_dump())

    # Get Achievements
    response = await client.get("/api/achievements", headers=headers)
    assert response.status_code == 200
    data = response.json()

    # Should have at least 1 unlocked (First Step)
    assert data["unlockedCount"] >= 1
    
    first_step = next((a for a in data["achievements"] if a["id"] == "first_show"), None)
    assert first_step is not None
    assert first_step["isUnlocked"] is True
