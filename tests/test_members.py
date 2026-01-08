import pytest
from httpx import AsyncClient

# Minimal test data
TEST_MEMBERS_DATA = [
    {
        "id": 76,
        "name": "Feni Fitriyanti",
        "nickname": "Feni",
        "generation": "3",
        "jiko": "Matahari yang indah!",
        "img": "https://example.com/feni.jpg",
        "active": True,
        "socials": {}
    },
    {
        "id": 999,
        "name": "Test Member",
        "nickname": "Tester",
        "generation": "12",
        "jiko": "Just a test",
        "img": "https://example.com/test.jpg",
        "active": True,
        "socials": {}
    }
]

@pytest.fixture
async def seed_members_db(db):
    """Seed the database with local test member data."""
    if TEST_MEMBERS_DATA:
        await db["members"].insert_many(TEST_MEMBERS_DATA)

@pytest.mark.asyncio
async def test_get_members_list(client: AsyncClient, seed_members_db):
    # Test List
    response = await client.get("/api/members")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0
    assert "meta" in data
    assert "total_data" in data["meta"]
    
    # Test Pagination
    response_limit = await client.get("/api/members?limit=5")
    # We only have 2 mock members
    assert len(response_limit.json()["data"]) == 2

@pytest.mark.asyncio
async def test_get_generations(client: AsyncClient, seed_members_db):
    response = await client.get("/api/members/generations")
    assert response.status_code == 200
    generations = response.json()
    assert isinstance(generations, list)
    assert len(generations) > 0
    # TEST_MEMBERS_DATA contains generation "3" and "12"
    assert "3" in generations or "12" in generations

@pytest.mark.asyncio
async def test_get_member_by_nickname(client: AsyncClient, seed_members_db):
    # Pick a known member from seed data
    # Feni is in the seed data
    nickname = "Feni"
    
    response = await client.get(f"/api/members/nickname/{nickname}")
    assert response.status_code == 200
    data = response.json()
    assert "member" in data
    assert data["member"]["nickname"] == nickname
    # Feni ID is 76
    assert data["member"]["id"] == 76

@pytest.mark.asyncio
async def test_get_member_by_id(client: AsyncClient, seed_members_db):
    # Feni ID is 76
    m_id = 76
    
    response = await client.get(f"/api/members/id/{m_id}")
    assert response.status_code == 200
    data = response.json()
    assert "member" in data
    assert data["member"]["id"] == m_id

@pytest.mark.asyncio
async def test_delete_member(client: AsyncClient, db, seed_members_db):
    """Test deleting a member (admin only)."""
    # First login as admin
    # Create admin user
    await db["users"].insert_one({
        "fullName": "Admin User",
        "memberId": "99999",
        "username": "adminuser",
        "email": "admin@example.com",
        "hashedPassword": "hashedpassword", # Mocked below since we use login endpoint which verifies
        "isEmailVerified": True,
        "role": "admin"
    })
    
    # We need to register properly to get a valid password hash or use the signup endpoint
    register_payload = {
        "fullName": "Admin User Test",
        "memberId": "88888",
        "username": "admintest",
        "email": "admintest@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "admintest"},
        {"$set": {"isEmailVerified": True, "isAdmin": True}}
    )

    login_res = await client.post("/api/auth/signin", data={
        "username": "admintest",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ID 76 is Feni (from TEST_MEMBERS_DATA)
    member_id = 76
    
    # Delete
    response = await client.delete(f"/api/members/{member_id}", headers=headers)
    assert response.status_code == 200
    # Check for standardized message
    assert response.json()["message"] == "Member deleted successfully."

    # Verify deleted
    get_res = await client.get(f"/api/members/id/{member_id}")
    assert get_res.status_code == 404

@pytest.mark.asyncio
async def test_create_member_forbidden(client: AsyncClient, db):
    """Test that non-admin users cannot create a member."""
    # Register Normal User
    register_payload = {
        "fullName": "Normal User Create",
        "memberId": "normcreate",
        "username": "normcreate",
        "email": "normcreate@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "normcreate"},
        {"$set": {"isEmailVerified": True}}
    )
    login_res = await client.post("/api/auth/signin", data={
        "username": "normcreate",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "New Member",
        "nickname": "New",
        "generation": "10"
    }
    response = await client.post("/api/members", json=payload, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_member_forbidden(client: AsyncClient, db):
    """Test that non-admin users cannot update a member."""
    # Register Normal User
    register_payload = {
        "fullName": "Normal User Update",
        "memberId": "normupdate",
        "username": "normupdate",
        "email": "normupdate@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "normupdate"},
        {"$set": {"isEmailVerified": True}}
    )
    login_res = await client.post("/api/auth/signin", data={
        "username": "normupdate",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ID 76 is Feni
    member_id = 76
    payload = {"name": "Updated Name"}
    response = await client.put(f"/api/members/{member_id}", json=payload, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_member_forbidden(client: AsyncClient, db):
    """Test that non-admin users cannot delete a member."""
    # Register Normal User
    register_payload = {
        "fullName": "Normal User Delete",
        "memberId": "normdelete",
        "username": "normdelete",
        "email": "normdelete@example.com",
        "password": "Password123!",
        "confirmPassword": "Password123!",
        "ofcStatus": "Active"
    }
    await client.post("/api/users/signup", json=register_payload)
    await db["users"].update_one(
        {"username": "normdelete"},
        {"$set": {"isEmailVerified": True}}
    )
    login_res = await client.post("/api/auth/signin", data={
        "username": "normdelete",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ID 76 is Feni
    member_id = 76
    response = await client.delete(f"/api/members/{member_id}", headers=headers)
    assert response.status_code == 403

