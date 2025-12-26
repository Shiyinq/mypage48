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
        "name": "Profile User",
        "username": "profileuser",
        "email": "profile@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!"
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
    assert data["username"] == "profileuser"
    assert data["email"] == "profile@example.com"
