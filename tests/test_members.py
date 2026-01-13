import pytest
from httpx import AsyncClient

# Minimal test data
# Minimal test data
TEST_MEMBERS_DATA = [
    {
        "id": "76",
        "name": "Feni Fitriyanti",
        "nickname": "Feni",
        "generation": "3",
        "jiko": "Matahari yang indah!",
        "img": "https://example.com/feni.jpg",
        "active": True,
        "socials": {}
    },
    {
        "id": "999",
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
    # Feni ID is "76"
    assert data["member"]["id"] == "76"

@pytest.mark.asyncio
async def test_get_member_by_id(client: AsyncClient, seed_members_db):
    # Feni ID is "76"
    m_id = "76"
    
    response = await client.get(f"/api/members/id/{m_id}")
    assert response.status_code == 200
    data = response.json()
    assert "member" in data
    assert data["member"]["id"] == m_id

@pytest.mark.asyncio
async def test_delete_member(client: AsyncClient, db, seed_members_db, create_user):
    """Test deleting a member (admin only)."""
    token, user_id, headers = await create_user("admintest", is_admin=True)

    # ID "76" is Feni (from TEST_MEMBERS_DATA)
    member_id = "76"
    
    # Delete
    response = await client.delete(f"/api/members/{member_id}", headers=headers)
    assert response.status_code == 200
    # Check for standardized message
    assert response.json()["message"] == "Member deleted successfully."

    # Verify deleted
    get_res = await client.get(f"/api/members/id/{member_id}")
    assert get_res.status_code == 404

@pytest.mark.asyncio
async def test_create_member_forbidden(client: AsyncClient, db, create_user):
    """Test that non-admin users cannot create a member."""
    token, user_id, headers = await create_user("normcreate")

    payload = {
        "name": "New Member",
        "nickname": "New",
        "generation": "10"
    }
    response = await client.post("/api/members", json=payload, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_member_forbidden(client: AsyncClient, db, create_user):
    """Test that non-admin users cannot update a member."""
    token, user_id, headers = await create_user("normupdate")

    # ID "76" is Feni
    member_id = "76"
    payload = {"name": "Updated Name"}
    response = await client.put(f"/api/members/{member_id}", json=payload, headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_member_forbidden(client: AsyncClient, db, create_user):
    """Test that non-admin users cannot delete a member."""
    token, user_id, headers = await create_user("normdelete")

    # ID "76" is Feni
    member_id = "76"
    response = await client.delete(f"/api/members/{member_id}", headers=headers)
    assert response.status_code == 403

