import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_seed_members(client: AsyncClient, db):
    # Ensure clean slate or just overwrite
    response = await client.post("/api/members/seed")
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert data["count"] > 0

@pytest.mark.asyncio
async def test_get_members_list(client: AsyncClient, db):
    # Ensure data exists
    await client.post("/api/members/seed")

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
    assert len(response_limit.json()["data"]) == 5

@pytest.mark.asyncio
async def test_get_generations(client: AsyncClient, db):
    await client.post("/api/members/seed")
    
    response = await client.get("/api/members/generations")
    assert response.status_code == 200
    generations = response.json()
    assert isinstance(generations, list)
    assert len(generations) > 0
    # Assuming "7" or "11" is in the seed data
    assert any(g for g in generations if str(g) in ["3", "7", "11", "12"])

@pytest.mark.asyncio
async def test_get_member_by_nickname(client: AsyncClient, db):
    await client.post("/api/members/seed")
    
    # Pick a known member from seed logic or just list and pick one
    list_res = await client.get("/api/members?limit=1")
    member = list_res.json()["data"][0]
    nickname = member["nickname"]
    
    response = await client.get(f"/api/members/nickname/{nickname}")
    assert response.status_code == 200
    data = response.json()
    assert "member" in data
    assert data["member"]["nickname"] == nickname
    assert data["member"]["id"] == member["id"]

@pytest.mark.asyncio
async def test_get_member_by_id(client: AsyncClient, db):
    await client.post("/api/members/seed")
    
    list_res = await client.get("/api/members?limit=1")
    member = list_res.json()["data"][0]
    m_id = member["id"]
    
    response = await client.get(f"/api/members/id/{m_id}")
    assert response.status_code == 200
    data = response.json()
    assert "member" in data
    assert data["member"]["id"] == m_id
