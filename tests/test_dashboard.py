"""Tests for Dashboard Service endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_dashboard_stats_unauthorized(client: AsyncClient, db):
    """Test that unauthenticated requests are rejected."""
    response = await client.get("/api/dashboard/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_dashboard_stats_empty(client: AsyncClient, db, create_user):
    """Test dashboard stats for user with no tickets."""
    token, user_id, headers = await create_user("dashboard_empty")

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
async def test_get_dashboard_stats_with_tickets(client: AsyncClient, db, create_user, create_ticket):
    """Test dashboard stats with ticket data."""
    token, user_id, headers = await create_user("dashboard_tickets")

    # Create test tickets
    await create_ticket(user_id, {
        "title": "Pajama Drive",
        "date": "2024-06-15",
        "section": "A1",
        "number": "5",
        "price": 50000,
    })
    await create_ticket(user_id, {
        "title": "Pajama Drive",
        "date": "2024-07-20",
        "section": "B2",
        "number": "10",
        "price": 60000,
    })
    await create_ticket(user_id, {
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
async def test_get_dashboard_stats_with_two_shot(client: AsyncClient, db, create_user, create_ticket):
    """Test dashboard stats with two-shot data."""
    token, user_id, headers = await create_user("dashboard_2shot")

    # Create tickets with two-shot
    await create_ticket(user_id, {
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
    await create_ticket(user_id, {
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
    await create_ticket(user_id, {
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
async def test_get_dashboard_stats_with_month_filter(client: AsyncClient, db, create_user, create_ticket):
    """Test dashboard stats with month range filter."""
    token, user_id, headers = await create_user("dashboard_month")

    # Create tickets across different months
    await create_ticket(user_id, {
        "title": "Show Jan",
        "date": "2024-01-15",
        "price": 50000,
    })
    await create_ticket(user_id, {
        "title": "Show Jun",
        "date": "2024-06-20",
        "price": 60000,
    })
    await create_ticket(user_id, {
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
async def test_get_dashboard_stats_all_data(client: AsyncClient, db, create_user, create_ticket):
    """Test dashboard stats with is_all_data flag."""
    token, user_id, headers = await create_user("dashboard_all")

    # Create tickets across different years
    await create_ticket(user_id, {
        "title": "Show 2023",
        "date": "2023-06-15",
        "price": 50000,
    })
    await create_ticket(user_id, {
        "title": "Show 2024",
        "date": "2024-06-20",
        "price": 60000,
    })
    await create_ticket(user_id, {
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
async def test_get_dashboard_stats_day_preference(client: AsyncClient, db, create_user, create_ticket):
    """Test dashboard day preference statistics."""
    token, user_id, headers = await create_user("dashboard_day")

    # Create tickets on different days
    await create_ticket(user_id, {
        "title": "Saturday Show 1",
        "date": "2024-06-15",
        "day": "Saturday",
        "price": 50000,
    })
    await create_ticket(user_id, {
        "title": "Saturday Show 2",
        "date": "2024-06-22",
        "day": "Saturday",
        "price": 60000,
    })
    await create_ticket(user_id, {
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
async def test_get_dashboard_stats_extremes(client: AsyncClient, db, create_user, create_ticket):
    """Test dashboard first/last show extremes."""
    token, user_id, headers = await create_user("dashboard_extremes")

    # Create tickets with different dates
    await create_ticket(user_id, {
        "title": "First Show",
        "date": "2024-01-15",
        "time": "14:00",
        "price": 50000,
    })
    await create_ticket(user_id, {
        "title": "Middle Show",
        "date": "2024-06-20",
        "time": "16:00",
        "price": 60000,
    })
    await create_ticket(user_id, {
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
