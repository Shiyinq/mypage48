"""Tests for Dashboard Service endpoints."""
import pytest
from httpx import AsyncClient


async def create_authenticated_user(client: AsyncClient, db, username: str, email: str):
    """Helper to register, verify, login a user and return token + user_id."""
    register_payload = {
        "fullName": f"Dashboard User",
        "memberId": username[:10],  # Keep memberId short
        "username": username,
        "email": email,
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)

    # Manually verify user
    await db["users"].update_one(
        {"username": username},
        {"$set": {"isEmailVerified": True}}
    )

    login_data = {"username": username, "password": "Password123!"}
    login_res = await client.post("/api/auth/signin", data=login_data)
    token = login_res.json()["access_token"]

    # Get user_id from profile - profile data is nested under 'profile' key
    headers = {"Authorization": f"Bearer {token}"}
    profile_res = await client.get("/api/users/profile", headers=headers)
    user_id = profile_res.json()["profile"]["userId"]

    return token, user_id, headers


async def create_test_ticket(db, user_id: str, ticket_data: dict):
    """Helper to create a test ticket."""
    from bson import ObjectId
    ticket = {
        "_id": ObjectId(),
        "user_id": user_id,  # Use snake_case to match repository query
        "event": {
            "title": ticket_data.get("title", "Pajama Drive"),
            "date": ticket_data.get("date", "2024-06-15"),
            "time": ticket_data.get("time", "14:00"),
            "day": ticket_data.get("day", "Saturday"),
        },
        "seat": {
            "section": ticket_data.get("section", "A1"),
            "number": ticket_data.get("number", "5"),
        },
        "price": ticket_data.get("price", 50000),
        "two_shot": ticket_data.get("two_shot", None),
    }
    await db["tickets"].insert_one(ticket)
    return str(ticket["_id"])


@pytest.mark.asyncio
async def test_get_dashboard_stats_unauthorized(client: AsyncClient, db):
    """Test that unauthenticated requests are rejected."""
    response = await client.get("/api/dashboard/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_dashboard_stats_empty(client: AsyncClient, db):
    """Test dashboard stats for user with no tickets."""
    token, user_id, headers = await create_authenticated_user(
        client, db, "dashboard_empty", "dashboard_empty@example.com"
    )

    response = await client.get("/api/dashboard/stats", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "available_years" in data
    assert "theater" in data
    assert "two_shot" in data
    assert "seat_map" in data
    assert "period" in data

    # Verify empty theater stats
    assert data["theater"]["total_visits"] == 0
    assert data["theater"]["total_spent"] == 0
    assert data["theater"]["most_frequent_row"] == "-"

    # Verify empty two_shot stats
    assert data["two_shot"]["total_count"] == 0
    assert data["two_shot"]["total_spend"] == 0


@pytest.mark.asyncio
async def test_get_dashboard_stats_with_tickets(client: AsyncClient, db):
    """Test dashboard stats with ticket data."""
    token, user_id, headers = await create_authenticated_user(
        client, db, "dashboard_tickets", "dashboard_tickets@example.com"
    )

    # Create test tickets
    await create_test_ticket(db, user_id, {
        "title": "Pajama Drive",
        "date": "2024-06-15",
        "section": "A1",
        "number": "5",
        "price": 50000,
    })
    await create_test_ticket(db, user_id, {
        "title": "Pajama Drive",
        "date": "2024-07-20",
        "section": "B2",
        "number": "10",
        "price": 60000,
    })
    await create_test_ticket(db, user_id, {
        "title": "Aitakatta",
        "date": "2024-08-10",
        "section": "A3",
        "number": "8",
        "price": 55000,
    })

    response = await client.get("/api/dashboard/stats?year=2024", headers=headers)
    assert response.status_code == 200

    data = response.json()

    # Verify theater stats
    assert data["theater"]["total_visits"] == 3
    assert data["theater"]["total_spent"] == 165000
    assert data["theater"]["top_show"]["title"] == "Pajama Drive"
    assert data["theater"]["top_show"]["count"] == 2

    # Verify seat map stats
    assert data["seat_map"]["row_stats"]["counts"]["A"] == 2
    assert data["seat_map"]["row_stats"]["counts"]["B"] == 1


@pytest.mark.asyncio
async def test_get_dashboard_stats_with_two_shot(client: AsyncClient, db):
    """Test dashboard stats with two-shot data."""
    token, user_id, headers = await create_authenticated_user(
        client, db, "dashboard_2shot", "dashboard_2shot@example.com"
    )

    # Create tickets with two-shot
    await create_test_ticket(db, user_id, {
        "title": "Pajama Drive",
        "date": "2024-06-15",
        "section": "A1",
        "number": "5",
        "price": 50000,
        "two_shot": {
            "member_name": "Shani",
            "price": 100000,
            "imageUrl": "https://example.com/shani.jpg",
        }
    })
    await create_test_ticket(db, user_id, {
        "title": "Aitakatta",
        "date": "2024-07-20",
        "section": "B2",
        "number": "10",
        "price": 60000,
        "two_shot": {
            "member_name": "Shani",
            "price": 100000,
            "imageUrl": "https://example.com/shani2.jpg",
        }
    })
    await create_test_ticket(db, user_id, {
        "title": "River",
        "date": "2024-08-10",
        "section": "C1",
        "number": "3",
        "price": 55000,
        "two_shot": {
            "member_name": "Zee",
            "price": 80000,
            "imageUrl": "https://example.com/zee.jpg",
        }
    })

    response = await client.get("/api/dashboard/stats?year=2024", headers=headers)
    assert response.status_code == 200

    data = response.json()

    # Verify two_shot stats
    assert data["two_shot"]["total_count"] == 3
    assert data["two_shot"]["total_spend"] == 280000
    assert data["two_shot"]["unique_count"] == 2
    assert data["two_shot"]["top_2_shot"]["name"] == "Shani"
    assert data["two_shot"]["top_2_shot"]["count"] == 2


@pytest.mark.asyncio
async def test_get_dashboard_stats_with_month_filter(client: AsyncClient, db):
    """Test dashboard stats with month range filter."""
    token, user_id, headers = await create_authenticated_user(
        client, db, "dashboard_month", "dashboard_month@example.com"
    )

    # Create tickets across different months
    await create_test_ticket(db, user_id, {
        "title": "Show Jan",
        "date": "2024-01-15",
        "price": 50000,
    })
    await create_test_ticket(db, user_id, {
        "title": "Show Jun",
        "date": "2024-06-20",
        "price": 60000,
    })
    await create_test_ticket(db, user_id, {
        "title": "Show Dec",
        "date": "2024-12-10",
        "price": 55000,
    })

    # Filter for June only (month 5 in 0-indexed)
    response = await client.get(
        "/api/dashboard/stats?year=2024&start_month=5&end_month=5",
        headers=headers
    )
    assert response.status_code == 200

    data = response.json()
    # Only June ticket should be counted
    assert data["theater"]["total_visits"] == 1
    assert data["theater"]["total_spent"] == 60000


@pytest.mark.asyncio
async def test_get_dashboard_stats_all_data(client: AsyncClient, db):
    """Test dashboard stats with is_all_data flag."""
    token, user_id, headers = await create_authenticated_user(
        client, db, "dashboard_all", "dashboard_all@example.com"
    )

    # Create tickets across different years
    await create_test_ticket(db, user_id, {
        "title": "Show 2023",
        "date": "2023-06-15",
        "price": 50000,
    })
    await create_test_ticket(db, user_id, {
        "title": "Show 2024",
        "date": "2024-06-20",
        "price": 60000,
    })
    await create_test_ticket(db, user_id, {
        "title": "Show 2025",
        "date": "2025-01-10",
        "price": 55000,
    })

    # Get all data regardless of year
    response = await client.get(
        "/api/dashboard/stats?is_all_data=true",
        headers=headers
    )
    assert response.status_code == 200

    data = response.json()
    assert data["theater"]["total_visits"] == 3
    assert data["theater"]["total_spent"] == 165000

    # Verify available years contains all years
    assert 2023 in data["available_years"]
    assert 2024 in data["available_years"]
    assert 2025 in data["available_years"]


@pytest.mark.asyncio
async def test_get_dashboard_stats_day_preference(client: AsyncClient, db):
    """Test dashboard day preference statistics."""
    token, user_id, headers = await create_authenticated_user(
        client, db, "dashboard_day", "dashboard_day@example.com"
    )

    # Create tickets on different days
    await create_test_ticket(db, user_id, {
        "title": "Saturday Show 1",
        "date": "2024-06-15",
        "day": "Saturday",
        "price": 50000,
    })
    await create_test_ticket(db, user_id, {
        "title": "Saturday Show 2",
        "date": "2024-06-22",
        "day": "Saturday",
        "price": 60000,
    })
    await create_test_ticket(db, user_id, {
        "title": "Sunday Show",
        "date": "2024-06-16",
        "day": "Sunday",
        "price": 55000,
    })

    response = await client.get("/api/dashboard/stats?year=2024", headers=headers)
    assert response.status_code == 200

    data = response.json()
    day_stats = data["period"]["day_stats"]["stats"]

    # Find Saturday and Sunday counts
    saturday_stat = next((d for d in day_stats if d["name"] == "Saturday"), None)
    sunday_stat = next((d for d in day_stats if d["name"] == "Sunday"), None)

    assert saturday_stat is not None
    assert saturday_stat["count"] == 2
    assert sunday_stat is not None
    assert sunday_stat["count"] == 1


@pytest.mark.asyncio
async def test_get_dashboard_stats_extremes(client: AsyncClient, db):
    """Test dashboard first/last show extremes."""
    token, user_id, headers = await create_authenticated_user(
        client, db, "dashboard_extremes", "dashboard_extremes@example.com"
    )

    # Create tickets with different dates
    await create_test_ticket(db, user_id, {
        "title": "First Show",
        "date": "2024-01-15",
        "time": "14:00",
        "price": 50000,
    })
    await create_test_ticket(db, user_id, {
        "title": "Middle Show",
        "date": "2024-06-20",
        "time": "16:00",
        "price": 60000,
    })
    await create_test_ticket(db, user_id, {
        "title": "Last Show",
        "date": "2024-12-25",
        "time": "19:00",
        "price": 55000,
    })

    response = await client.get("/api/dashboard/stats?year=2024", headers=headers)
    assert response.status_code == 200

    data = response.json()
    extremes = data["theater"]["extremes"]

    assert extremes["first"]["title"] == "First Show"
    assert extremes["last"]["title"] == "Last Show"
