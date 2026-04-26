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
async def test_get_events_paginated(client, create_event, create_user):
    # Auth
    _, _, headers = await create_user("testuser")

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

    response = await client.get("/api/events/?page=1&limit=10", headers=headers)
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
async def test_get_current_events(client, create_event, create_user):
    # Auth
    _, _, headers = await create_user("testuser")

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
    
    response = await client.get("/api/events/current?page=1&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert data["meta"]["total_data"] == 1
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "future-1"


@pytest.mark.asyncio
async def test_events_sorting(client, create_event, create_user):
    # Auth
    _, _, headers = await create_user("testuser")

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
    response = await client.get("/api/events/?page=1&limit=10", headers=headers)
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
    response = await client.get("/api/events/current?page=1&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    ids = [e["id"] for e in data]
    
    assert ids == ["future-soon", "future-later"]


@pytest.mark.asyncio
async def test_get_events_with_aggregation(client, create_event, db, create_user):
    # Auth
    _, _, headers = await create_user("testuser")

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
    
    response = await client.get("/api/events/?page=1&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    
    event = next(e for e in data if e["id"] == "event-agg")
    
    # Verify flattened aggregation
    assert "img" in event.get("imageUrl")
    assert event.get("imageUrl_medium") is not None
    assert event.get("imageUrl_small") is not None
    assert event.get("totalMembers") == 1
    
    assert event.get("memberIds") is None or event.get("memberIds") == []


@pytest.mark.asyncio
async def test_get_calendar_events(client, create_event, create_user, db):
    # Auth
    _, _, headers = await create_user("testuser")

    # Setup - Insert member for seitansai lookup
    await db["members"].insert_one({
        "id": "member-A",
        "name": "Member A",
        "nickname": "MemA"
    })

    # Setup test data
    # Target month: Feb 2026
    year, month = 2026, 2
    
    # Events within range (Feb 2026)
    await create_event({
        "id": "cal-1",
        "title": "Feb Event 1",
        "date": "2026-02-01T12:00:00",
        "url": "/link",
        "label": "",
        "setlistId": "s1",
        "seitansaiIds": ["member-A"]
    })
    
    # Event in adjacent month (Jan 2026) - Should be included if within grid range (last week of Jan)
    # 2026-02-01 is Sunday. So grid starts exactly on Feb 1st (if Sunday start) or earlier.
    # Service logic: first_of_month = Feb 1. weekday() for Feb 1 2026.
    # Let's assume standard logic includes some previous days.
    # Wait, 2026-02-01 is a Sunday. If Sunday is start of week (0), then start_date is Feb 1.
    # If Monday is start (0), Sunday is 6.
    # Service uses: (first_of_month.weekday() + 1) % 7.
    # Python weekday: Mon=0, Sun=6.
    # Feb 1 2026 is Sunday. weekday()=6.
    # (6 + 1) % 7 = 0. So days_to_subtract = 0. Start Date = Feb 1.
    # So Jan events strictly won't show up in this specific month case.
    
    # Let's try March. Feb 2026 has 28 days.
    # 42 days from Feb 1 cover all Feb + first 2 weeks of March.
    # Event in March (within 42 days range)
    await create_event({
        "id": "cal-2",
        "title": "Mar Event (In Grid)",
        "date": "2026-03-05T12:00:00",
        "url": "/link",
        "label": ""
    })
    
    # Event way outside
    await create_event({
        "id": "cal-out",
        "title": "Way Outside",
        "date": "2026-05-01T12:00:00",
        "url": "/link",
        "label": ""
    })
    
    response = await client.get(f"/api/events/calendar?year={year}&month={month}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    titles = [e["title"] for e in data]
    assert "Feb Event 1" in titles
    assert "Mar Event (In Grid)" in titles
    assert "Way Outside" not in titles
    
    # Verify Schema Optimization
    event = next(e for e in data if e["title"] == "Feb Event 1")
    # Should NOT have detail fields
    assert "imageUrl" not in event or event["imageUrl"] is None
    assert "totalMembers" not in event or event.get("totalMembers", 0) == 0
    # Should have calendar fields
    assert event["setlistId"] == "s1"
    assert event["seitansaiMembers"] == ["Member A"]


@pytest.mark.asyncio
async def test_get_events_paginated_error(client, monkeypatch, create_user):
    # Auth
    _, _, headers = await create_user("testuser")

    from src.events.service import EventsService
    
    # Mock repository method to raise generic exception
    async def mock_find(*args, **kwargs):
        raise Exception("DB Error")
        
    monkeypatch.setattr("src.events.repository.EventsRepository.find_events_paginated", mock_find)
    monkeypatch.setattr("src.events.repository.EventsRepository.count_events", mock_find)
    
    # Depending on where count is called first
    response = await client.get("/api/events/", headers=headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to fetch event data."


@pytest.mark.asyncio
async def test_get_calendar_events_error(client, monkeypatch, create_user):
    # Auth
    _, _, headers = await create_user("testuser")

    from src.events.service import EventsService
    
    async def mock_find_range(*args, **kwargs):
        raise Exception("DB Error")
    
    monkeypatch.setattr("src.events.repository.EventsRepository.find_events_by_date_range", mock_find_range)
    
    response = await client.get("/api/events/calendar?year=2026&month=2", headers=headers)
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to fetch event data."


@pytest.mark.asyncio
async def test_get_calendar_events_with_birthdays(client, create_user, db):
    # Auth
    _, _, headers = await create_user("testuser")

    # Insert a member with a birthday in Feb
    await db["members"].insert_one({
        "id": "member-bday",
        "name": "Birthday Girl",
        "birthdate": "14 Februari 2000",
        "active": True
    })

    # Call calendar for Feb 2026
    year, month = 2026, 2
    
    # 2026-02-14 is within the range
    response = await client.get(f"/api/events/calendar?year={year}&month={month}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    titles = [e["title"] for e in data]
    assert "Birthday Girl" in titles
    
    # Verify Birthday Event Structure
    bday_event = next(e for e in data if e["title"] == "Birthday Girl")
    assert bday_event["isBirthday"] is True
    assert bday_event["date"].startswith("2026-02-14")
    assert bday_event["url"] == "/member/detail/id/member-bday"


@pytest.mark.asyncio
async def test_get_calendar_events_with_cross_month_birthdays(client, create_user, db):
    # Testing the user request about "next month preview"
    # Feb 2026 calendar (28 days). 
    # Starts Feb 1 (Sunday). 
    # 42 days grid -> Ends mid March.
    
    # Insert a member with birthday in early March
    # Auth
    _, _, headers = await create_user("testuser2")

    await db["members"].insert_one({
        "id": "member-march-bday",
        "name": "March Baby",
        "birthdate": "5 Maret 2000",
        "active": True
    })
    
    # Call calendar for Feb 2026
    # 5 March 2026 should be visible in the Feb view (since it covers 42 days)
    year, month = 2026, 2
    response = await client.get(f"/api/events/calendar?year={year}&month={month}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    titles = [e["title"] for e in data]
    assert "March Baby" in titles
