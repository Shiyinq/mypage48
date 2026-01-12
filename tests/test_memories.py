import pytest
from httpx import AsyncClient
from datetime import datetime
from src.tickets.schemas import TicketInDB, TicketEvent, TicketSeat, TicketTwoShot


@pytest.mark.asyncio
async def test_get_memories_unauthorized(client: AsyncClient):
    response = await client.get("/api/memories")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_memories_empty(client: AsyncClient, db, create_user):
    """Test getting memories with no tickets."""
    token, user_id, headers = await create_user("memoryuser")

    # Get Memories (Empty - no tickets with images)
    response = await client.get("/api/memories", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["total_data"] == 0
    assert len(data["data"]) == 0


@pytest.mark.asyncio
async def test_get_memories_with_images(client: AsyncClient, db, create_user):
    """Test getting memories with ticket images."""
    token, user_id, headers = await create_user("memoryuser2")

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
        imageUrl="data:image/png;base64,iVBORw0KGgo=",
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
async def test_get_memories_with_2shot(client: AsyncClient, db, create_user):
    """Test getting memories with 2shot images."""
    token, user_id, headers = await create_user("memoryuser3")

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


@pytest.mark.asyncio
async def test_get_top_two_shot(client: AsyncClient, db, create_user):
    """Test getting top two shot statistics."""
    token, user_id, headers = await create_user("memoryuser4")

    # Insert multiple tickets with 2-shot info for ranking
    tickets = [
        TicketInDB(
            user_id=user_id,
            ticket_id="T1",
            event=TicketEvent(title="Show1", date="2023-01-01", day="Sun", time="14:00"),
            seat=TicketSeat(section="A", number=1),
            price=150000,
            two_shot=TicketTwoShot(member_name="Freya Jayawardana", price=50000, type="Roulette"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        TicketInDB(
            user_id=user_id,
            ticket_id="T2",
            event=TicketEvent(title="Show2", date="2023-01-02", day="Mon", time="19:00"),
            seat=TicketSeat(section="A", number=2),
            price=150000,
            two_shot=TicketTwoShot(member_name="Freya Jayawardana", price=60000, type="Birthday"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        TicketInDB(
            user_id=user_id,
            ticket_id="T3",
            event=TicketEvent(title="Show3", date="2023-01-03", day="Tue", time="19:00"),
            seat=TicketSeat(section="A", number=3),
            price=150000,
            two_shot=TicketTwoShot(member_name="Angelina Christy", price=50000, type="Roulette"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]
    
    for t in tickets:
        await db["tickets"].insert_one(t.model_dump())

    # Call API
    response = await client.get("/api/memories/top-two-shot", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "ranking" in data
    assert "totalTwoShotSpend" in data
    assert "totalTwoShotCount" in data

    # Verify Totals (50000 + 60000 + 50000 = 160000)
    assert data["totalTwoShotSpend"] == 160000
    assert data["totalTwoShotCount"] == 3

    # Verify Ranking
    ranking = data["ranking"]
    assert len(ranking) >= 2
    
    # Freya should be #1
    assert ranking[0]["name"] == "Freya Jayawardana"
    assert ranking[0]["count"] == 2
    assert ranking[0]["spend"] == 110000
    
    # Christy should be #2
    assert ranking[1]["name"] == "Angelina Christy"
    assert ranking[1]["count"] == 1
    assert ranking[1]["spend"] == 50000
