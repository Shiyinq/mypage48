import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_advanced_ticket_filters(client: AsyncClient, db):
    # Setup user
    register_payload = {
        "fullName": "Filter User",
        "memberId": "filt123",
        "username": "filteruser",
        "email": "filter@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    await db["users"].update_one(
        {"username": "filteruser"}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    login_res = await client.post("/api/auth/signin", data={"username": "filteruser", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create dummy tickets
    # 1. 2-shot ticket on Monday
    t1 = {
        "ticket_id": "T-1",
        "event": {
            "title": "Show A",
            "date": "2024-01-01", # Monday
            "day": "Monday",
            "time": "19:00",
            "gate_open": "18:30"
        },
        "seat": {"section": "A", "number": "1"},
        "price": 100,
        "two_shot": {
            "member_name": "Member A",
            "type": "Roulette",
            "price": 500
        }
    }
    # 2. No 2-shot on Sunday
    t2 = {
        "ticket_id": "T-2",
        "event": {
            "title": "Show B",
            "date": "2024-01-07", # Sunday
            "day": "Sunday",
            "time": "14:00",
            "gate_open": "13:30"
        },
        "seat": {"section": "B", "number": "1"},
        "price": 100
    }
    # 3. No 2-shot on Monday, Title "Show A Special"
    t3 = {
        "ticket_id": "T-3",
        "event": {
            "title": "Show A Special",
            "date": "2024-01-08", # Monday
            "day": "Monday",
            "time": "19:00",
            "gate_open": "18:30"
        },
        "seat": {"section": "A", "number": "2"},
        "price": 100
    }

    await client.post("/api/theater/tickets", json=t1, headers=headers)
    await client.post("/api/theater/tickets", json=t2, headers=headers)
    await client.post("/api/theater/tickets", json=t3, headers=headers)

    # Test 1: Filter by Title "Show A" (should match T1 and T3)
    res = await client.get("/api/theater/tickets?title=Show A", headers=headers)
    data = res.json()["data"]
    assert len(data) == 2
    titles = sorted([t["event"]["title"] for t in data])
    assert titles == ["Show A", "Show A Special"]

    # Test 2: Filter by Title exact enough to exclude one
    res = await client.get("/api/theater/tickets?title=Special", headers=headers)
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["event"]["title"] == "Show A Special"

    # Test 3: Filter by Has 2-shot (should match T1)
    res = await client.get("/api/theater/tickets?has_two_shot=true", headers=headers)
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["ticket_id"] == "T-1"

    # Test 4: Filter by Days (Monday) (should match T1 and T3)
    # FastAPI handles list query params as same-key multiple values: ?days=Monday
    res = await client.get("/api/theater/tickets?days=Monday", headers=headers)
    data = res.json()["data"]
    assert len(data) == 2
    for t in data:
        assert t["event"]["day"] == "Monday"

    # Test 5: Filter by Days (Sunday)
    res = await client.get("/api/theater/tickets?days=Sunday", headers=headers)
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["event"]["day"] == "Sunday"

    # Test 6: Filter by Date Range (2024-01-01 to 2024-01-05) -> T1 only
    res = await client.get("/api/theater/tickets?start_date=2024-01-01&end_date=2024-01-05", headers=headers)
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["ticket_id"] == "T-1"

    # Test 7: Combined Filters (Monday AND No 2-shot) -> Wait, how to say 'no 2 shot'?
    # API only supports has_two_shot=true. If omitted, it returns all.
    # Current implementation: if has_two_shot=None (default), logic is skipped -> all.
    # User requirement likely was 'show me tickets that have 2shots'.
    # If they want ONLY non-2shots, we didn't implement that. We implemented "Enable filter to show only 2-shots".
    # Let's test combined: Title "Show A" AND has_two_shot=true -> T1
    res = await client.get("/api/theater/tickets?title=Show A&has_two_shot=true", headers=headers)
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["ticket_id"] == "T-1"
