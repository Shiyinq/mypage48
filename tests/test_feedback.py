import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_submit_feedback_success(client: AsyncClient):
    payload = {
        "type": "issue",
        "message": "This is a test feedback message that is long enough.",
        "email": "test@example.com",
        "name": "Test User"
    }
    response = await client.post("/api/feedback", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == payload["message"]
    assert data["type"] == payload["type"]
    assert "id" in data
    assert "created_at" in data

@pytest.mark.asyncio
async def test_submit_feedback_validation_error(client: AsyncClient):
    # Message too short (< 10 chars)
    payload = {
        "type": "issue",
        "message": "Short",
        "email": "test@example.com"
    }
    response = await client.post("/api/feedback", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_feedback_admin_success(client: AsyncClient, create_user):
    # Create admin user
    token, _, headers = await create_user("adminuser", is_admin=True)

    # Helper to submit feedback first
    await client.post("/api/feedback", json={
        "type": "suggestion",
        "message": "Test feedback 1 for list",
        "email": "u1@e.com"
    })

    response = await client.get("/api/feedback", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 1
    assert data["page"] == 1

@pytest.mark.asyncio
async def test_get_feedback_forbidden_non_admin(client: AsyncClient, create_user):
    # Create normal user
    token, _, headers = await create_user("normaluser", is_admin=False)

    response = await client.get("/api/feedback", headers=headers)
    assert response.status_code == 403
