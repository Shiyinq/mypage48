import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_read_users_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/users/profile")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_read_users_me_success(client: AsyncClient, db):
    # Register and Login to get token
    register_payload = {
        "fullName": "Profile User",
        "memberId": "12345",
        "username": "profileuser",
        "email": "profile@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)

    # Manually verify user in DB
    await db["users"].update_one(
        {"username": "profileuser"}, 
        {"$set": {"isEmailVerified": True}}
    )

    login_data = {
        "username": "profileuser",
        "password": "Password123!"
    }
    login_res = await client.post("/api/auth/signin", data=login_data)
    token = login_res.json()["access_token"]

    # Get Profile
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/users/profile", headers=headers)
    assert response.status_code == 200
    data = response.json()
    # Profile data is now nested under 'profile' key in ProfileFullResponse
    profile = data["profile"]
    assert profile["username"] == "profileuser"
    assert profile["email"] == "profile@example.com"
    # Note: DB might store 'name' instead of 'fullName' depending on mapping, 
    # but the input was fullName. UserCurrent schema (response) likely has 'name'.
    assert profile["name"] == "Profile User"

@pytest.mark.asyncio
async def test_update_oshi(client: AsyncClient, db):
    # Register and Login
    register_payload = {
        "fullName": "Oshi User",
        "memberId": "oshi123",
        "username": "oshiuser",
        "email": "oshi@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    await db["users"].update_one(
        {"username": "oshiuser"}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    login_res = await client.post("/api/auth/signin", data={"username": "oshiuser", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update Oshi
    oshi_payload = {"oshiId": 1}
    response = await client.post("/api/users/oshi", json=oshi_payload, headers=headers)
    assert response.status_code == 200
    
    # Verify profile update
    profile_res = await client.get("/api/users/profile", headers=headers)
    # Profile data is now nested under 'profile' key in ProfileFullResponse
    assert profile_res.json()["profile"]["oshiId"] == 1

@pytest.mark.asyncio
async def test_update_public_status(client: AsyncClient, db):
    # Register and Login
    register_payload = {
        "fullName": "Public User",
        "memberId": "pub123",
        "username": "publicuser",
        "email": "public@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    await db["users"].update_one(
        {"username": "publicuser"}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    login_res = await client.post("/api/auth/signin", data={"username": "publicuser", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update Public Status
    status_payload = {"isPublic": True, "publicYear": 2024}
    response = await client.post("/api/users/public-status", json=status_payload, headers=headers)
    assert response.status_code == 200
    
    # Verify profile
    profile_res = await client.get("/api/users/profile", headers=headers)
    data = profile_res.json()
    # Profile data is now nested under 'profile' key in ProfileFullResponse
    profile = data["profile"]
    assert profile["isPublic"] is True
    assert profile["publicYear"] == 2024

@pytest.mark.asyncio
async def test_update_profile_picture(client: AsyncClient, db):
    # Register and Login
    register_payload = {
        "fullName": "Pic User",
        "memberId": "pic123",
        "username": "picuser",
        "email": "pic@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    await db["users"].update_one(
        {"username": "picuser"}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    login_res = await client.post("/api/auth/signin", data={"username": "picuser", "password": "Password123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Use a minimal valid PNG image (1x1 pixel transparent)
    # This is a valid base64-encoded PNG file
    valid_png_base64 = (
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAA"
        "DUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    
    # Update Profile Picture
    pic_payload = {"profilePicture": valid_png_base64}
    response = await client.post("/api/users/profile-picture", json=pic_payload, headers=headers)
    assert response.status_code == 200
    
    # Verify profile
    profile_res = await client.get("/api/users/profile", headers=headers)
    # Profile data is now nested under 'profile' key in ProfileFullResponse
    assert profile_res.json()["profile"]["profilePicture"] == valid_png_base64

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
