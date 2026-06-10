import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_read_users_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/users/profile")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_read_users_me_success(client: AsyncClient, db, create_user):
    """Test getting user profile with valid token."""
    token, user_id, headers = await create_user("profileuser", full_name="Profile User")

    # Get Profile
    response = await client.get("/api/users/profile", headers=headers)
    assert response.status_code == 200
    data = response.json()
    # Profile data is now nested under 'profile' key in ProfileFullResponse
    profile = data["profile"]
    assert profile["username"] == "profileuser"
    assert profile["email"] == "profileuser@example.com"
    assert profile["name"] == "Profile User"

@pytest.mark.asyncio
async def test_get_all_users_admin(client: AsyncClient, db, create_user):
    """Test getting all users as admin."""
    token, user_id, headers = await create_user("adminlist", is_admin=True)

    # Get All Users
    response = await client.get("/api/users", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0
    assert "meta" in data

@pytest.mark.asyncio
async def test_get_all_users_forbidden(client: AsyncClient, db, create_user):
    """Test that non-admin users cannot get all users."""
    token, user_id, headers = await create_user("normaluser")

    # Get All Users -> Should fail
    response = await client.get("/api/users", headers=headers)
    assert response.status_code == 403
@pytest.mark.asyncio
async def test_update_oshi(client: AsyncClient, db, create_user):
    """Test updating user's oshi."""
    token, user_id, headers = await create_user("oshiuser")

    # Update Oshi
    oshi_payload = {"oshiId": 1}
    response = await client.post("/api/users/oshi", json=oshi_payload, headers=headers)
    assert response.status_code == 200
    
    # Verify in DB directly (profile endpoint uses stale current_user from JWT)
    user = await db["users"].find_one({"userId": user_id})
    assert user["oshiId"] == "1"

@pytest.mark.asyncio
async def test_update_public_status(client: AsyncClient, db, create_user):
    """Test updating user's public status."""
    token, user_id, headers = await create_user("publicuser")

    # Update Public Status
    status_payload = {"isPublic": True, "publicYear": 2024}
    response = await client.post("/api/users/public-status", json=status_payload, headers=headers)
    assert response.status_code == 200
    
    # Verify in DB directly (profile endpoint uses stale current_user from JWT)
    user = await db["users"].find_one({"userId": user_id})
    assert user["isPublic"] is True
    assert user["publicYear"] == 2024

@pytest.mark.asyncio
async def test_update_profile_picture(client: AsyncClient, db, create_user):
    """Test updating user's profile picture."""
    token, user_id, headers = await create_user("picuser")

    # Update Profile Picture (simulating saving a storage path)
    dummy_path = "avatar/user_id/test_image.webp"
    pic_payload = {"profilePicture": dummy_path}
    response = await client.post("/api/users/profile-picture", json=pic_payload, headers=headers)
    assert response.status_code == 200
    
    # Verify in DB directly
    user = await db["users"].find_one({"userId": user_id})
    assert user["profilePicture"] == dummy_path

@pytest.mark.asyncio
async def test_update_profile_picture_validation(client: AsyncClient, db, create_user):
    """Test validation of profile picture path and length."""
    token, user_id, headers = await create_user("valuser")

    # 1. Test missing prefix
    pic_payload = {"profilePicture": "wrong/path/image.webp"}
    response = await client.post("/api/users/profile-picture", json=pic_payload, headers=headers)
    assert response.status_code == 422
    assert "Profile picture image path must start with 'avatar/'" in response.text

    # 2. Test exceeding length (100)
    long_path = "avatar/" + "a" * 100
    pic_payload = {"profilePicture": long_path}
    response = await client.post("/api/users/profile-picture", json=pic_payload, headers=headers)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_public_profile(client: AsyncClient, db):
    # Register a user who is public
    register_payload = {
        "fullName": "Visible User",
        "username": "visibleuser",
        "email": "visible@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    # Set public status in DB directly or via API
    await db["users"].update_one(
        {"username": "visibleuser"}, 
        {"$set": {"isPublic": True, "isEmailVerified": True}}
    )

    # Get Public Profile
    response = await client.get("/api/u/visibleuser")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "visibleuser"
    assert data["name"] == "Visible User"

@pytest.mark.asyncio
async def test_oshi_meetings_logic(client: AsyncClient, db, create_user, create_ticket):
    """Test calculation of Oshi Meetings (attendance at events where Oshi was present)."""
    from datetime import datetime
    
    # 1. Create user
    token, user_id, headers = await create_user("meetinguser")
    
    # 2. Set Oshi (Member ID: "123")
    oshi_id = "123"
    await db["users"].update_one(
        {"userId": user_id},
        {"$set": {"oshiId": oshi_id}}
    )
    
    # Mock Oshi Member Data (needed for profile endpoint to resolve Oshi name)
    await db["members"].insert_one({
        "id": oshi_id,
        "name": "My Oshi",
        "nickname": "Oshi",
        "img": "http://example.com/img.jpg",
        "generation": "1",
        "jiko": "Oshi desu",
        "socials": {}
    })
    
    # 3. Create Events
    # Event 1: Oshi Present
    await db["events"].insert_one({
        "title": "Event A",
        "date": datetime(2024, 1, 1),
        "memberIds": [oshi_id, "999"],
        "url": "http://example.com/a",
        "label": "Theater",
        "setlistId": "s1"
    })
    
    # Event 2: Oshi Not Present
    await db["events"].insert_one({
        "title": "Event B",
        "date": datetime(2024, 1, 2),
        "memberIds": ["999"],
        "url": "http://example.com/b",
        "label": "Theater",
        "setlistId": "s1"
    })
    
    # Event 3: Oshi Present but User Not Attended
    await db["events"].insert_one({
        "title": "Event C",
        "date": datetime(2024, 1, 3),
        "memberIds": [oshi_id],
        "url": "http://example.com/c",
        "label": "Theater",
        "setlistId": "s1"
    })

    # 4. Create Tickets
    # Ticket for Event 1 (Match)
    await create_ticket(user_id, {
        "title": "Event A",
        "date": "2024-01-01"
    })
    
    # Ticket for Event 2 (No Match - Oshi absent)
    await create_ticket(user_id, {
        "title": "Event B",
        "date": "2024-01-02"
    })
    
    # Ticket for random event (No Match - Event doesn't exist in DB)
    await create_ticket(user_id, {
        "title": "Event D",
        "date": "2024-01-04"
    })

    # 5. Call Profile Endpoint
    response = await client.get("/api/users/profile", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Extract stats (stats is a top-level field in ProfileFullResponse)
    stats = data["stats"]

    # Verify Oshi Meetings
    # Should be 1 (Event A)
    assert stats["oshiMeetings"] == 1
    assert stats["totalShows"] == 3

    # Verify Oshi Schedule Structure
    oshi_data = data["oshi"]
    assert oshi_data is not None
    assert "upcomingSchedule" in oshi_data
    assert "pastSchedule" in oshi_data
    assert isinstance(oshi_data["upcomingSchedule"], list)
    assert isinstance(oshi_data["pastSchedule"], list)

    # Since all events are in 2024 and current date is (presumably) later or events are just past,
    # we expect them to populate appropriately.
    # event A (2024-01-01) and event C (2024-01-03) are for Oshi "123".
    # Since current time is > 2024, they should be in pastSchedule.
    assert len(oshi_data["pastSchedule"]) > 0
    # Check that Event A or C is in pastSchedule
    past_titles = [s["title"] for s in oshi_data["pastSchedule"]]
    assert "Event A" in past_titles
    assert "Event C" in past_titles


@pytest.mark.asyncio
async def test_total_two_shots(client: AsyncClient, db, create_user, create_ticket):
    """Test calculation of totalTwoShots in profile stats."""
    token, user_id, headers = await create_user("twoshotuser")

    # Create tickets: 3 with two_shot, 2 without
    await create_ticket(user_id, {
        "title": "Show A",
        "date": "2024-01-01",
        "two_shot": {"member_name": "Member A", "type": "Roulette", "price": 50000, "imageUrl": "http://example.com/a.jpg"}
    })
    await create_ticket(user_id, {
        "title": "Show B",
        "date": "2024-01-02",
        "two_shot": {"member_name": "Member B", "type": "Birthday", "price": 50000, "imageUrl": "http://example.com/b.jpg"}
    })
    await create_ticket(user_id, {
        "title": "Show C",
        "date": "2024-01-03",
        "two_shot": {"member_name": "Member A", "type": "Roulette", "price": 50000, "imageUrl": "http://example.com/c.jpg"}
    })
    await create_ticket(user_id, {
        "title": "Show D",
        "date": "2024-01-04",
        "two_shot": None
    })
    await create_ticket(user_id, {
        "title": "Show E",
        "date": "2024-01-05",
        "two_shot": None
    })

    response = await client.get("/api/users/profile", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["stats"]["totalShows"] == 5
    assert data["stats"]["totalTwoShots"] == 3


@pytest.mark.asyncio
async def test_total_live_watched(client: AsyncClient, db, create_user):
    """Test calculation of totalLiveWatched from watched_live_history."""
    from datetime import datetime

    token, user_id, headers = await create_user("livewatcher")

    # Insert watched live history entries for this user
    watched_entries = [
        {
            "user_id": user_id,
            "live_id": f"live_{i}",
            "member_id": f"member_{i}",
            "member_name": f"Member {i}",
            "platform": "showroom",
            "duration": 300,
            "started_at": datetime(2024, 6, 1, 10, 0, 0),
            "last_updated_at": datetime(2024, 6, 1, 10, 5, 0),
        }
        for i in range(5)
    ]
    await db["watched_live_history"].insert_many(watched_entries)

    # Insert an entry for a different user (should not be counted)
    await db["watched_live_history"].insert_one({
        "user_id": "other_user",
        "live_id": "live_other",
        "member_id": "member_other",
        "member_name": "Other",
        "platform": "idn",
        "duration": 600,
        "started_at": datetime(2024, 6, 1, 11, 0, 0),
        "last_updated_at": datetime(2024, 6, 1, 11, 10, 0),
    })

    response = await client.get("/api/users/profile", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["stats"]["totalLiveWatched"] == 5
