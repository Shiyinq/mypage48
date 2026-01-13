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

    # Use a minimal valid PNG image (1x1 pixel transparent)
    valid_png_base64 = (
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAA"
        "DUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    
    # Update Profile Picture
    pic_payload = {"profilePicture": valid_png_base64}
    response = await client.post("/api/users/profile-picture", json=pic_payload, headers=headers)
    assert response.status_code == 200
    
    # Verify in DB directly (profile endpoint uses stale current_user from JWT)
    user = await db["users"].find_one({"userId": user_id})
    assert user["profilePicture"] == valid_png_base64

@pytest.mark.asyncio
async def test_get_public_profile(client: AsyncClient, db):
    # Register a user who is public
    register_payload = {
        "fullName": "Visible User",
        "memberId": "vis123",
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
