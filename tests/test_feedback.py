import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_submit_feedback_success(client: AsyncClient, create_user):
    token, _, headers = await create_user("feeduser1")
    payload = {
        "type": "issue",
        "message": "This is a test feedback message that is long enough.",
        "email": "test@example.com",
        "name": "Test User"
    }
    response = await client.post("/api/feedback", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == payload["message"]
    assert data["type"] == payload["type"]
    assert "id" in data
    assert "created_at" in data

@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_submit_feedback_validation_error(client: AsyncClient, create_user):
    token, _, headers = await create_user("feeduser2")
    # Message too short (< 10 chars)
    payload = {
        "type": "issue",
        "message": "Short",
        "email": "test@example.com"
    }
    response = await client.post("/api/feedback", json=payload, headers=headers)
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
    }, headers=headers)

    response = await client.get("/api/feedback", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["current_page"] == 1


@pytest.mark.asyncio
async def test_get_feedback_admin_filter(client: AsyncClient, create_user):
    token, _, headers = await create_user("adminfilter", is_admin=True)

    # Submit 2 feedbacks
    res1 = await client.post("/api/feedback", json={
        "type": "issue", "message": "Feedback A", "email": "a@e.com"
    }, headers=headers)
    res2 = await client.post("/api/feedback", json={
        "type": "issue", "message": "Feedback B", "email": "b@e.com"
    }, headers=headers)
    
    # Update one to implemented
    await client.patch(f"/api/feedback/{res2.json()['id']}/status", json={
        "status": "implemented", "admin_notes": ""
    }, headers=headers)

    # Filter pending
    res_pending = await client.get("/api/feedback?status=pending", headers=headers)
    assert res_pending.status_code == 200
    assert len(res_pending.json()["data"]) == 1
    assert res_pending.json()["data"][0]["status"] == "pending"

    # Filter multiple (implemented & pending)
    res_multi = await client.get("/api/feedback?status=pending&status=implemented", headers=headers)
    assert res_multi.status_code == 200
    assert len(res_multi.json()["data"]) >= 2

@pytest.mark.asyncio
async def test_get_feedback_invalid_status_filter(client: AsyncClient, create_user):
    token, _, headers = await create_user("adminfilter_invalid", is_admin=True)

    # Filter with invalid status
    response = await client.get("/api/feedback?status=invalid_status", headers=headers)
    assert response.status_code == 422
    assert "detail" in response.json()

@pytest.mark.asyncio
async def test_get_feedback_forbidden_non_admin(client: AsyncClient, create_user):
    # Create normal user
    token, _, headers = await create_user("normaluser", is_admin=False)

    response = await client.get("/api/feedback", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_my_feedback(client: AsyncClient, create_user):
    token, _, headers = await create_user("myfeedbackuser")
    
    # Submit one feedback
    await client.post("/api/feedback", json={
        "type": "issue",
        "message": "My own feedback item here",
        "email": "my@e.com"
    }, headers=headers)

    response = await client.get("/api/feedback/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1
    assert data["data"][0]["message"] == "My own feedback item here"

@pytest.mark.asyncio
async def test_update_feedback_status(client: AsyncClient, create_user):
    # Create admin user
    token, user, headers = await create_user("adminstatus", is_admin=True)

    # Submit feedback
    post_res = await client.post("/api/feedback", json={
        "type": "suggestion",
        "message": "A suggestion to be updated",
        "email": "adminstatus@e.com"
    }, headers=headers)
    
    feedback_id = post_res.json()["id"]

    # Update status
    update_payload = {
        "status": "implemented",
        "admin_notes": "We did it!"
    }
    patch_res = await client.patch(f"/api/feedback/{feedback_id}/status", json=update_payload, headers=headers)
    
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["status"] == "implemented"
    assert data["admin_notes"] == "We did it!"


@pytest.mark.asyncio
async def test_delete_feedback_success(client: AsyncClient, create_user):
    token, user, headers = await create_user("deletefeedbackuser")

    # Submit feedback
    post_res = await client.post("/api/feedback", json={
        "type": "issue",
        "message": "To be deleted",
        "email": "del@example.com"
    }, headers=headers)
    
    feedback_id = post_res.json()["id"]

    # Delete feedback
    del_res = await client.delete(f"/api/feedback/{feedback_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify deleted
    get_res = await client.get("/api/feedback/me", headers=headers)
    assert len(get_res.json()["data"]) == 0


@pytest.mark.asyncio
async def test_delete_feedback_forbidden(client: AsyncClient, create_user):
    token1, user1, headers1 = await create_user("user_a")
    token2, user2, headers2 = await create_user("user_b")

    # User A submits feedback
    post_res = await client.post("/api/feedback", json={
        "type": "suggestion",
        "message": "User A suggestion",
        "email": "a@example.com"
    }, headers=headers1)
    
    feedback_id = post_res.json()["id"]

    # User B tries to delete User A's feedback
    del_res = await client.delete(f"/api/feedback/{feedback_id}", headers=headers2)
    assert del_res.status_code == 404  # Service raises FeedbackNotFound to prevent enumeration
