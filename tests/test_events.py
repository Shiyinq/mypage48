import pytest
from datetime import datetime, timedelta

@pytest.fixture
def create_event(db):
    """
    Factory fixture to create test events directly in the database.
    """
    async def _create(event_data: dict) -> str:
        if "date" in event_data and isinstance(event_data["date"], str):
             event_data["date"] = datetime.fromisoformat(event_data["date"])
        
        await db["events"].insert_one(event_data)
        return event_data["id"]
    
    return _create

@pytest.mark.asyncio
async def test_get_events_paginated(client, create_event):
    # Create mixed events
    # Future event (Basic type)
    await create_event({
        "id": "basic-event-1",
        "label": "/images/icon.cat2.png",
        "title": "Basic Event Future",
        "url": "/calendar/1",
        "date": "2026-02-07T00:00:00"
    })
    
    # Past event (Detail type)
    await create_event({
        "id": "detail-event-1",
        "setlistId": "setlist1",
        "title": "Detail Event Past",
        "team": {"id": "team7", "img": "img.png"},
        "graduationIds": [],
        "date": "2020-01-01T19:00:00",
        "memberIds": ["1", "2"],
        "seitansaiIds": [],
        "url": "/theater/schedule/1",
        "label": "/images/icon.cat17.png"
    })

    response = await client.get("/api/events/?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    
    # Check pagination structure
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["total_data"] == 2
    assert len(data["data"]) == 2
    
    # Verify data unification
    events = {e["id"]: e for e in data["data"]}
    assert "basic-event-1" in events
    assert "detail-event-1" in events
    
    basic = events["basic-event-1"]
    assert basic["title"] == "Basic Event Future"
    # Optional fields should be present as null/empty if handled by schema default
    assert basic.get("setlistId") is None
    
    detail = events["detail-event-1"]
    assert detail["setlistId"] == "setlist1"
    assert detail["team"]["id"] == "team7"


@pytest.mark.asyncio
async def test_get_current_events(client, create_event):
    now = datetime.now()
    future_date = now + timedelta(days=10)
    past_date = now - timedelta(days=10)
    
    # Future event
    await create_event({
        "id": "future-1",
        "title": "Future Event",
        "date": future_date.isoformat(),
        "url": "/link",
        "label": "lbl"
    })
    
    # Past event
    await create_event({
        "id": "past-1",
        "title": "Past Event",
        "date": past_date.isoformat(),
        "url": "/link",
        "label": "lbl"
    })
    
    response = await client.get("/api/events/current?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()
    
    assert data["meta"]["total_data"] == 1
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "future-1"


@pytest.mark.asyncio
async def test_events_sorting(client, create_event):
    now = datetime.now()
    
    # Create events with specific dates
    # Past events
    await create_event({"id": "past-old", "title": "Oldest", "date": (now - timedelta(days=2)).isoformat(), "url": "/", "label": ""})
    await create_event({"id": "past-recent", "title": "Recent Past", "date": (now - timedelta(days=1)).isoformat(), "url": "/", "label": ""})
    
    # Future events
    await create_event({"id": "future-soon", "title": "Sooner", "date": (now + timedelta(days=1)).isoformat(), "url": "/", "label": ""})
    await create_event({"id": "future-later", "title": "Later", "date": (now + timedelta(days=2)).isoformat(), "url": "/", "label": ""})
    
    # 1. Test History (All events) -> Should be Descending (Latest first)
    # Expected order: future-later, future-soon, past-recent, past-old
    response = await client.get("/api/events/?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()["data"]
    ids = [e["id"] for e in data]
    
    # Note: Depending on implementation, "All events" might just be everything.
    # Our requirement was "event history" to be sorted by latest.
    # Usually "history" implies everything or past. The endpoint is /api/events/ which returns all.
    # Sort order -1 (descending) means largest date (future) first.
    assert ids == ["future-later", "future-soon", "past-recent", "past-old"]
    
    # 2. Test Current (Upcoming) -> Should be Ascending (Soonest first)
    # Expected order: future-soon, future-later
    response = await client.get("/api/events/current?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()["data"]
    ids = [e["id"] for e in data]
    
    assert ids == ["future-soon", "future-later"]


@pytest.mark.asyncio
async def test_get_events_with_aggregation(client, create_event, db):
    # Setup - Insert related data
    await db["setlists"].insert_one({
        "setlistId": "setlist-agg",
        "title": "Aggregated Setlist",
        "imageUrl": "img",
        "description": "desc",
        "type": "setlist",
        "active": True
    })
    
    await db["members"].insert_one({
        "id": "member-1",
        "name": "Member One",
        "nickname": "Mem1"
    })
    
    # Create event linking to them
    await create_event({
        "id": "event-agg",
        "title": "Event with Aggregation",
        "date": "2026-03-01T00:00:00",
        "url": "/link",
        "label": "lbl",
        "setlistId": "setlist-agg",
        "memberIds": ["member-1"]
    })
    
    response = await client.get("/api/events/?page=1&limit=10")
    assert response.status_code == 200
    data = response.json()["data"]
    
    event = next(e for e in data if e["id"] == "event-agg")
    
    # Verify flattened aggregation
    assert event.get("imageUrl") == "img"
    assert event.get("totalMembers") == 1
    
    # Verify removed/excluded fields
    # Note: These might be present as None depending on schema, but logically we check for absence of full object
    assert event.get("setlist") is None
    assert event.get("members") is None or event.get("members") == []
    assert event.get("memberIds") is None or event.get("memberIds") == []
