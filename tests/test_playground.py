import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_playground_openapi_access_success(client: AsyncClient, create_user):
    """
    Test that an authenticated user can successully access the playground OpenAPI schema.
    """
    _, _, headers = await create_user("playground_tester")
    
    response = await client.get("/api/playground/openapi.json", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    assert data["info"]["title"] == "MyPage48 Public API Playground"

@pytest.mark.asyncio
async def test_playground_openapi_tag_filtering(client: AsyncClient, create_user):
    """
    Test that sensitive tags (Auth, API Keys, Feedback) are filtered out.
    """
    _, _, headers = await create_user("tag_tester")
    
    response = await client.get("/api/playground/openapi.json", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    excluded_tags = {"Auth", "API Keys", "Feedback"}
    
    for path, methods in data["paths"].items():
        for method, details in methods.items():
            tags = details.get("tags", [])
            for tag in tags:
                assert tag not in excluded_tags, f"Leaked tag '{tag}' in path {path}"

@pytest.mark.asyncio
async def test_playground_openapi_endpoint_filtering(client: AsyncClient, create_user):
    """
    Test that specific sensitive endpoints are blacklisted.
    """
    _, _, headers = await create_user("endpoint_tester")
    
    response = await client.get("/api/playground/openapi.json", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    paths = data["paths"]
    
    # Specific endpoints to check
    excluded_endpoints = [
        "/api/users",
        "/api/users/signup",
        "/api/users/profile-picture",
    ]
    
    for excluded in excluded_endpoints:
        # Check if the path exists exactly or as a prefix in more complex cases
        # But here the playground filters exact matches from request.app.routes
        assert excluded not in paths, f"Leaked excluded endpoint: {excluded}"

@pytest.mark.asyncio
async def test_playground_openapi_admin_filtering(client: AsyncClient, create_user):
    """
    Test that routes requiring admin privileges are excluded.
    """
    _, _, headers = await create_user("admin_tester")
    
    response = await client.get("/api/playground/openapi.json", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    paths = data["paths"]
    
    # Check for known admin endpoints (e.g., in achievements or storage)
    # Achievement sync is admin only
    assert "/api/achievements/sync" not in paths
    # Storage settings or similar might be admin only
    # Let's check some common ones
    assert "/api/admin" not in paths
    # Achievement sync is a good one to check as it's defined in AchievementsRouter with require_admin
    
@pytest.mark.asyncio
async def test_playground_unauthorized_access(client: AsyncClient):
    """
    Test that unauthenticated users cannot access the schema.
    """
    response = await client.get("/api/playground/openapi.json")
    # Should be 401 Unauthorized
    assert response.status_code == 401
