import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pymongo.errors import ConnectionFailure
from fastapi import status

from src.health.constants import HealthStatus, DatabaseStatus
from src.database import database_instance
from src.main import app
from src.dependencies import get_storage_repository

@pytest.fixture
def mock_storage_repo():
    mock = AsyncMock()
    mock.check_connection.return_value = True
    return mock

@pytest.mark.asyncio
async def test_health_check_success(client, mock_storage_repo):
    """
    Test health check endpoint returns 200 OK when database is connected.
    """
    app.dependency_overrides[get_storage_repository] = lambda: mock_storage_repo
    
    try:
        response = await client.get("/api/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == HealthStatus.OK
        assert data["database"] == DatabaseStatus.CONNECTED
        assert data["storage"] == DatabaseStatus.CONNECTED
        assert data["detail"] is None
    finally:
        app.dependency_overrides.pop(get_storage_repository, None)

@pytest.mark.asyncio
async def test_health_check_db_failure(client, mock_storage_repo):
    """
    Test health check endpoint returns 503 Service Unavailable when database ping fails.
    """
    app.dependency_overrides[get_storage_repository] = lambda: mock_storage_repo
    
    # Mock the ping command to raise ConnectionFailure
    # We need to patch the client on the database_instance
    
    # Save original client
    original_client = database_instance.client
    
    # Create a mock client that raises exception on admin.command("ping")
    mock_client = AsyncMock()
    mock_client.admin.command.side_effect = ConnectionFailure("Mock connection failure")
    
    # Temporarily replace client
    database_instance.client = mock_client
    
    try:
        response = await client.get("/api/health")
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["status"] == HealthStatus.ERROR
        assert data["database"] == DatabaseStatus.ERROR
        assert data["storage"] == DatabaseStatus.CONNECTED
        assert "Database: Mock connection failure" in data["detail"]
        
    finally:
        # Restore original client
        database_instance.client = original_client
        app.dependency_overrides.pop(get_storage_repository, None)

@pytest.mark.asyncio
async def test_health_check_minio_failure(client):
    """
    Test health check endpoint returns 503 when Storage check fails.
    """
    mock_storage_fail = AsyncMock()
    mock_storage_fail.check_connection.return_value = False
    
    app.dependency_overrides[get_storage_repository] = lambda: mock_storage_fail
    
    try:
        response = await client.get("/api/health")
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["status"] == HealthStatus.ERROR
        assert data["database"] == DatabaseStatus.CONNECTED
        assert data["storage"] == DatabaseStatus.DISCONNECTED
        # Detail might differ depending on implementation, for now let's just check status
        
    finally:
        app.dependency_overrides.pop(get_storage_repository, None)

@pytest.mark.asyncio
async def test_record_recorder_heartbeat_success(client, create_user, db):
    """
    Test recorder heartbeat endpoint succeeds for admin users.
    """
    _, _, headers = await create_user("healthadmin", is_admin=True)
    
    payload = {
        "mode": "all",
        "bot_token": "some_token",
        "chat_id": "some_id"
    }
    
    response = await client.post("/api/health/recorder", json=payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
    
    # Verify in DB
    heartbeat = await db["recorder_heartbeats"].find_one({"_id": "recorder_all"})
    assert heartbeat is not None
    assert heartbeat["mode"] == "all"
    assert heartbeat["encrypted_bot_token"] is not None
    assert heartbeat["encrypted_bot_token"] != "some_token"

@pytest.mark.asyncio
async def test_record_recorder_heartbeat_unauthorized(client, create_user):
    """
    Test recorder heartbeat endpoint fails for non-admin users.
    """
    _, _, headers = await create_user("healthuser", is_admin=False)
    
    payload = {
        "mode": "all",
        "bot_token": "some_token",
        "chat_id": "some_id"
    }
    
    response = await client.post("/api/health/recorder", json=payload, headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
