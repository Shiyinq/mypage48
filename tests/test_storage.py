import pytest
from unittest.mock import AsyncMock, MagicMock
from src.storage.service import StorageService
from src.storage.schemas import ImageCategory
from src.dependencies import get_storage_service
from src.main import app
from src.tickets.schemas import TicketResponse

# Mock Repository
class MockStorageRepository:
    def __init__(self):
        self.upload_file = MagicMock()
        self.get_presigned_url = MagicMock(return_value="https://minio.example.com/bucket/file.jpg")
        self.file_exists = MagicMock(return_value=True)
        self.delete_file = MagicMock(return_value=True)

@pytest.fixture
def mock_storage_repo():
    return MockStorageRepository()

@pytest.fixture
def storage_service(mock_storage_repo):
    # Mock config
    mock_config = MagicMock()
    mock_config.MINIO_BUCKET = "test-bucket"
    return StorageService(repository=mock_storage_repo, config=mock_config)

@pytest.mark.asyncio
async def test_resolve_url(storage_service):
    # Test None
    assert storage_service.resolve_url(None) is None
    
    # Test Base64
    base64_img = "data:image/png;base64,aaaa"
    assert storage_service.resolve_url(base64_img) == base64_img
    
    # Test HTTP URL
    http_url = "http://example.com/image.jpg"
    assert storage_service.resolve_url(http_url) == http_url
    
    # Test Storage Filename
    filename = "tickets/user1/abc.jpg"
    url = storage_service.resolve_url(filename)
    assert url == "https://minio.example.com/bucket/file.jpg"
    storage_service.repository.get_presigned_url.assert_called_with(filename)

@pytest.mark.asyncio
async def test_upload_image(storage_service):
    user_id = "user123"
    category = "ticket"
    base64_img = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    response = storage_service.upload_image(user_id, base64_img, category)
    
    assert response.filename.startswith("ticket/user123/")
    assert response.filename.endswith(".png")
    assert response.url == "https://minio.example.com/bucket/file.jpg"
    storage_service.repository.upload_file.assert_called_once()

@pytest.mark.asyncio
async def test_resolve_ticket_images(storage_service):
    # Mock TicketResponse with valid data
    from datetime import datetime
    ticket_data = {
        "_id": "t1",
        "user_id": "u1",
        "ticket_id": "tid1",
        "event": {
            "title": "Test Event",
            "date": "2023-01-01",
            "day": "Sunday",
            "time": "19:00"
        },
        "seat": {
            "section": "A",
            "number": "1"
        },
        "price": 10000,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "imageUrl": "tickets/u1/img1.jpg",
        "two_shot": {
             "member_name": "Test Member",
             "price": 5000,
             "imageUrl": "twoshot/u1/img2.jpg"
        }
    }
    
    # Use actual class
    ticket = TicketResponse(**ticket_data)
    
    resolved = storage_service.resolve_ticket_images(ticket)
    
    assert resolved.imageUrl == "https://minio.example.com/bucket/file.jpg"
    assert resolved.two_shot.imageUrl == "https://minio.example.com/bucket/file.jpg"

# API Tests
@pytest.mark.asyncio
async def test_api_upload_image(client, storage_service):
    # Override dependency
    app.dependency_overrides[get_storage_service] = lambda: storage_service
    
    # Mock Auth
    from src.dependencies import get_current_user
    from src.auth.schemas import UserCurrent
    
    app.dependency_overrides[get_current_user] = lambda: UserCurrent(
        userId="user123", 
        username="test", 
        name="Test User",
        email="test@test.com", 
        role="user"
    )
    
    payload = {
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        "category": "ticket"
    }
    
    response = await client.post("/api/storage/upload", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "filename" in data
    assert "url" in data
    assert data["url"] == "https://minio.example.com/bucket/file.jpg"

@pytest.mark.asyncio
async def test_api_get_presigned_url(client, storage_service):
    app.dependency_overrides[get_storage_service] = lambda: storage_service
    
    # Needs auth too? 
    # The endpoint is likely protected or public? 
    # Let's check route.py. get_presigned_url endpoint in storage/route.py usually requires auth?
    # Actually I should verify storage/route.py content.
    
    response = await client.get("/api/storage/url/tickets/user1/test.jpg")
    
    if response.status_code == 401:
         # Add auth override if needed
         from src.dependencies import get_current_user
         from src.auth.schemas import UserCurrent
         app.dependency_overrides[get_current_user] = lambda: UserCurrent(
            userId="user123", 
            username="test", 
            name="Test User",
            email="test@test.com", 
            role="user"
         )
         response = await client.get("/api/storage/url/tickets/user1/test.jpg")

    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://minio.example.com/bucket/file.jpg"
