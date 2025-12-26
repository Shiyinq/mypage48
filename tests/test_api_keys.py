import pytest
from httpx import AsyncClient
from src.config import config

@pytest.mark.asyncio
async def test_create_api_key_success(client: AsyncClient, db):
    # Register and Login
    register_payload = {
        "name": "ApiKey User",
        "username": "apikeyuser",
        "email": "apikey@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!"
    }
    await client.post("/api/users/signup", json=register_payload)

    # Manually verify user
    await db["users"].update_one(
        {"username": "apikeyuser"}, 
        {"$set": {"isEmailVerified": True}}
    )

    login_data = {
        "username": "apikeyuser",
        "password": "Password123!"
    }
    login_res = await client.post("/api/auth/signin", data=login_data)
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create API Key
    response = await client.post("/api/key", headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "apiKey" in data
    assert data["apiKey"].startswith(config.api_key_prefix)

@pytest.mark.asyncio
async def test_use_api_key_success(client: AsyncClient, db):
    # Register and Login
    register_payload = {
        "name": "ApiKey Use User",
        "username": "apikeyuse",
        "email": "apikeyuse@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    # Manually verify user
    await db["users"].update_one(
        {"username": "apikeyuse"}, 
        {"$set": {"isEmailVerified": True}}
    )
    
    login_data = {"username": "apikeyuse", "password": "Password123!"}
    login_res = await client.post("/api/auth/signin", data=login_data)
    token = login_res.json()["access_token"]
    
    # Create API Key
    headers_token = {"Authorization": f"Bearer {token}"}
    key_res = await client.post("/api/key", headers=headers_token)
    api_key = key_res.json()["apiKey"]

    # Use API Key to access profile
    headers_key = {"Authorization": f"Bearer {api_key}"}
    response = await client.get("/api/users/profile", headers=headers_key)
    assert response.status_code == 200
    assert response.json()["username"] == "apikeyuse"

@pytest.mark.asyncio
async def test_revoke_api_key(client: AsyncClient, db):
    # Register and Create Key
    register_payload = {
        "name": "Revoke User",
        "username": "revokeuser",
        "email": "revoke@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!"
    }
    await client.post("/api/users/signup", json=register_payload)
    
    # Manually verify user
    await db["users"].update_one(
        {"username": "revokeuser"}, 
        {"$set": {"isEmailVerified": True}}
    )

    login_data = {"username": "revokeuser", "password": "Password123!"}
    login_res = await client.post("/api/auth/signin", data=login_data)
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    key_res = await client.post("/api/key", headers=headers)
    api_key = key_res.json()["apiKey"]

    # Revoke (Delete) Key
    del_res = await client.delete("/api/key", headers=headers)
    assert del_res.status_code == 200
    
    # Try to use revoked key
    headers_key = {"Authorization": f"Bearer {api_key}"}
    # Should be 400 because InvalidJWTToken maps to 400 in this project
    response = await client.get("/api/users/profile", headers=headers_key)
    assert response.status_code == 401
