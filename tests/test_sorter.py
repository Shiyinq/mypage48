import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_save_sorter_success(client: AsyncClient, db, create_user):
    """Test saving a sorter history."""
    token, user_id, headers = await create_user("sorteruser")

    payload = {
        "title": "Oshi Sorter Kece",
        "description": "Ini adalah peringkat oshi terbaikku!",
        "filters": ["Gen 13", "Gen 12"],
        "results": [
            {"id": "m1", "name": "Jacqueline Immanuela", "rank": 1},
            {"id": "m2", "name": "Aurellia", "rank": 2},
        ],
    }

    response = await client.post(
        "/api/theater/sorter", json=payload, headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Oshi Sorter Kece"
    assert data["description"] == "Ini adalah peringkat oshi terbaikku!"
    assert data["filters"] == ["Gen 13", "Gen 12"]
    assert len(data["results"]) == 2
    assert data["results"][0]["id"] == "m1"
    assert data["results"][0]["name"] == "Jacqueline Immanuela"
    assert data["results"][0]["rank"] == 1
    assert "_id" in data


@pytest.mark.asyncio
async def test_save_sorter_unauthorized(client: AsyncClient, db):
    """Test saving sorter history without authentication."""
    payload = {"title": "Unauthorized Sorter", "results": []}
    response = await client.post("/api/theater/sorter", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_sorters(client: AsyncClient, db, create_user):
    """Test getting saved sorters."""
    token, user_id, headers = await create_user("getsortersuser")

    payload1 = {
        "title": "Sorter 1",
        "filters": ["Gen 13"],
        "results": [{"id": "m1", "name": "Jacqueline Immanuela", "rank": 1}],
    }
    payload2 = {
        "title": "Sorter 2",
        "filters": ["Gen 14"],
        "results": [{"id": "m2", "name": "Feni", "rank": 1}],
    }

    await client.post("/api/theater/sorter", json=payload1, headers=headers)
    await client.post("/api/theater/sorter", json=payload2, headers=headers)

    response = await client.get("/api/theater/sorter", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 2
    assert data["data"][0]["title"] == "Sorter 2"
    assert data["data"][1]["title"] == "Sorter 1"


@pytest.mark.asyncio
async def test_get_sorter_detail(client: AsyncClient, db, create_user):
    """Test getting specific sorter details."""
    token, user_id, headers = await create_user("detailuser")

    payload = {
        "title": "Detail Sorter",
        "results": [{"id": "m1", "name": "Jacqueline Immanuela", "rank": 1}],
    }
    res = await client.post(
        "/api/theater/sorter", json=payload, headers=headers
    )
    sorter_id = res.json()["_id"]

    response = await client.get(
        f"/api/theater/sorter/{sorter_id}", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Detail Sorter"
    assert data["results"][0]["id"] == "m1"

    # Unauthorized access check: another user cannot access this sorter
    token2, user_id2, headers2 = await create_user("anotheruser")
    response2 = await client.get(
        f"/api/theater/sorter/{sorter_id}", headers=headers2
    )
    assert response2.status_code == 404


@pytest.mark.asyncio
async def test_delete_sorter(client: AsyncClient, db, create_user):
    """Test deleting a sorter."""
    token, user_id, headers = await create_user("deluser")

    payload = {"title": "Delete Me", "results": []}
    res = await client.post(
        "/api/theater/sorter", json=payload, headers=headers
    )
    sorter_id = res.json()["_id"]

    # Delete
    response = await client.delete(
        f"/api/theater/sorter/{sorter_id}", headers=headers
    )
    assert response.status_code == 204

    # Verify 404
    response_get = await client.get(
        f"/api/theater/sorter/{sorter_id}", headers=headers
    )
    assert response_get.status_code == 404


@pytest.mark.asyncio
async def test_update_sorter(client: AsyncClient, db, create_user):
    """Test updating a sorter."""
    token, user_id, headers = await create_user("updateuser")

    payload = {"title": "Original Title", "description": "Original description", "results": []}
    res = await client.post(
        "/api/theater/sorter", json=payload, headers=headers
    )
    sorter_id = res.json()["_id"]

    # Update title and description
    update_payload = {"title": "Updated Title", "description": "Updated description"}
    response = await client.patch(
        f"/api/theater/sorter/{sorter_id}", json=update_payload, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"

    # Verify update in get
    response_get = await client.get(
        f"/api/theater/sorter/{sorter_id}", headers=headers
    )
    assert response_get.status_code == 200
    assert response_get.json()["title"] == "Updated Title"

    # Unauthorized access check
    token2, user_id2, headers2 = await create_user("anotheruser2")
    response2 = await client.patch(
        f"/api/theater/sorter/{sorter_id}", json=update_payload, headers=headers2
    )
    assert response2.status_code == 404

