import pytest
from httpx import AsyncClient
from datetime import datetime

TEST_MEMBERS_DATA = [
    {
        "id": "76",
        "name": "Feni Fitriyanti",
        "nickname": "Feni",
        "generation": "3",
        "jiko": "Matahari yang indah!",
        "img": "https://example.com/feni.jpg",
        "active": True,
        "socials": {},
        # Set birthdate to today/tomorrow dynamically would be better, but for simplicity we'll check schema
        "birthdate": "16 Januari 1999",
        "member_type": "JKT48",
        "member_code": "FENI"
    },
    {
        "id": "999",
        "name": "Test Member",
        "nickname": "Tester",
        "generation": "12",
        "jiko": "Just a test",
        "img": "https://example.com/test.jpg",
        "active": True,
        "socials": {},
        "birthdate": f"{datetime.now().day} {datetime.now().strftime('%B')} 2000".replace("January","Januari").replace("February","Februari").replace("March","Maret").replace("April","April").replace("May","Mei").replace("June","Juni").replace("July","Juli").replace("August","Agustus").replace("September","September").replace("October","Oktober").replace("November","November").replace("December","Desember"),
        "member_type": "Trainee",
        "member_code": "TEST"
    }
]

@pytest.fixture
async def seed_members_db(db):
    """Seed the database with local test member data."""
    if TEST_MEMBERS_DATA:
        await db["members"].insert_many(TEST_MEMBERS_DATA)

@pytest.mark.asyncio
async def test_get_upcoming_birthdays(client: AsyncClient, seed_members_db, create_user):
    # Auth
    token, user_id, headers = await create_user("bdayuser")
    
    response = await client.get("/api/members/birthdays", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # The second mock member is dynamically set to have a birthday today, so it should be in the list
    assert len(data) >= 1
    
    first = data[0]
    assert "days_until" in first
    assert "age" in first
    assert "birthdate" in first

@pytest.mark.asyncio
async def test_get_members_list(client: AsyncClient, seed_members_db, create_user):
    # Auth
    token, user_id, headers = await create_user("listuser")

    # Test List
    response = await client.get("/api/members", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0
    assert "meta" in data
    assert "total_data" in data["meta"]
    
    # Assert new fields are present
    first_member = data["data"][0]
    assert "member_type" in first_member
    assert "member_code" in first_member
    
    # Test Pagination
    response_limit = await client.get("/api/members?limit=5", headers=headers)
    # We only have 2 mock members
    assert len(response_limit.json()["data"]) == 2

@pytest.mark.asyncio
async def test_get_generations(client: AsyncClient, seed_members_db, create_user):
    # Auth
    token, user_id, headers = await create_user("genuser")

    response = await client.get("/api/members/generations", headers=headers)
    assert response.status_code == 200
    generations = response.json()
    assert isinstance(generations, list)
    assert len(generations) > 0
    # TEST_MEMBERS_DATA contains generation "3" and "12"
    assert "3" in generations or "12" in generations

@pytest.mark.asyncio
async def test_get_member_by_nickname(client: AsyncClient, seed_members_db, create_user):
    # Auth
    token, user_id, headers = await create_user("nickuser")

    # Pick a known member from seed data
    # Feni is in the seed data
    nickname = "Feni"
    
    response = await client.get(f"/api/members/nickname/{nickname}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "member" in data
    assert data["member"]["nickname"] == nickname
    # Feni ID is "76"
    assert data["member"]["id"] == "76"

@pytest.mark.asyncio
async def test_get_member_by_id(client: AsyncClient, seed_members_db, create_user):
    # Auth
    token, user_id, headers = await create_user("iduser")

    # Feni ID is "76"
    m_id = "76"
    
    response = await client.get(f"/api/members/id/{m_id}", headers=headers)
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
    get_res = await client.get(f"/api/members/id/{member_id}", headers=headers)
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

