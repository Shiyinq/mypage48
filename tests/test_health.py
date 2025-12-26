import pytest
from unittest.mock import AsyncMock, patch
from pymongo.errors import ConnectionFailure
from fastapi import status

from src.health.constants import HealthStatus, DatabaseStatus
from src.database import database_instance

@pytest.mark.asyncio
async def test_health_check_success(client):
    """
    Test health check endpoint returns 200 OK when database is connected.
    """
    response = await client.get("/api/health")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == HealthStatus.OK
    assert data["database"] == DatabaseStatus.CONNECTED
    assert data["detail"] is None

@pytest.mark.asyncio
async def test_health_check_db_failure(client):
    """
    Test health check endpoint returns 503 Service Unavailable when database ping fails.
    """
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
        assert "Database connection failure" in data["detail"]
        
    finally:
        # Restore original client
        database_instance.client = original_client
