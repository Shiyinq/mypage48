import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_get_dashboard_users_unauthorized(client: AsyncClient):
    res = await client.get("/api/admin/dashboard/users")
    assert res.status_code == 404

async def test_get_dashboard_users_forbidden(client: AsyncClient, create_user):
    _, _, headers = await create_user("normal_user_1", is_admin=False)
    res = await client.get("/api/admin/dashboard/users", headers=headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "Not Found"

async def test_get_dashboard_users_success(client: AsyncClient, create_user):
    _, _, headers = await create_user("admin_user_1", is_admin=True)
    res = await client.get("/api/admin/dashboard/users", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_users" in data
    assert "verified_users" in data
    assert "users_joined_today" in data

async def test_get_dashboard_mypage_unauthorized(client: AsyncClient):
    res = await client.get("/api/admin/dashboard/mypage")
    assert res.status_code == 404

async def test_get_dashboard_mypage_forbidden(client: AsyncClient, create_user):
    _, _, headers = await create_user("normal_user_2", is_admin=False)
    res = await client.get("/api/admin/dashboard/mypage", headers=headers)
    assert res.status_code == 404

async def test_get_dashboard_mypage_success(client: AsyncClient, create_user):
    _, _, headers = await create_user("admin_user_2", is_admin=True)
    res = await client.get("/api/admin/dashboard/mypage", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_tickets" in data
    assert "total_2shot" in data

async def test_get_dashboard_theater_unauthorized(client: AsyncClient):
    res = await client.get("/api/admin/dashboard/theater")
    assert res.status_code == 404

async def test_get_dashboard_theater_forbidden(client: AsyncClient, create_user):
    _, _, headers = await create_user("normal_user_3", is_admin=False)
    res = await client.get("/api/admin/dashboard/theater", headers=headers)
    assert res.status_code == 404

async def test_get_dashboard_theater_success(client: AsyncClient, create_user):
    _, _, headers = await create_user("admin_user_3", is_admin=True)
    res = await client.get("/api/admin/dashboard/theater", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_members_jkt" in data
    assert "active_members_count" in data
