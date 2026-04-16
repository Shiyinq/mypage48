import pytest
import io
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
		self.get_file_with_metadata = MagicMock(return_value=(b"fake_image_content", "image/jpeg"))
		self.get_file_stream_with_metadata = MagicMock(return_value=(io.BytesIO(b"fake_image_content"), "image/jpeg"))

@pytest.fixture
def mock_storage_repo():
    return MockStorageRepository()

@pytest.fixture
def storage_service(mock_storage_repo):
    # Mock config
    mock_config = MagicMock()
    mock_config.MINIO_BUCKET = "test-bucket"
    mock_config.secret_key = "test-secret-key-for-hmac-signing-purposes"
    mock_config.algorithm = "HS256"
    mock_config.api_base_url = "http://localhost:8080/api"
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
    assert "/api/storage/m/tickets/user1/abc.jpg" in url
    assert "expires=" in url
    assert "signature=" in url

@pytest.mark.asyncio
async def test_upload_image(storage_service):
    user_id = "user123"
    category = "ticket"
    base64_img = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    response = storage_service.upload_image(user_id, base64_img, category)
    
    assert response.filename.startswith("ticket/user123/")
    assert response.filename.endswith(".png")
    assert "/api/storage/m/" in response.url
    assert "signature=" in response.url
    storage_service.repository.upload_file.assert_called_once()

@pytest.mark.asyncio
async def test_upload_image_journal(storage_service):
    user_id = "user123"
    category = "journal"
    base64_img = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    response = storage_service.upload_image(user_id, base64_img, category)
    
    assert response.filename.startswith("journal/user123/")
    assert response.filename.endswith(".png")
    assert "/api/storage/m/" in response.url

@pytest.mark.asyncio
async def test_get_bulk_presigned_urls(storage_service):
    filenames = ["journal/u1/1.jpg", "ticket/u1/2.png"]
    
    response = storage_service.get_bulk_presigned_urls(filenames)
    
    assert len(response.urls) == 2
    assert "/api/storage/m/" in response.urls["journal/u1/1.jpg"]
    assert "/api/storage/m/" in response.urls["ticket/u1/2.png"]
    assert response.expires_in == 3600

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
    
    assert "/api/storage/m/tickets/u1/img1.jpg" in resolved.imageUrl
    assert "/api/storage/m/twoshot/u1/img2.jpg" in resolved.two_shot.imageUrl

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
    
    try:
        payload = {
            "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
            "category": "ticket"
        }
        
        response = await client.post("/api/storage/upload", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "filename" in data
        assert "url" in data
        assert "/api/storage/m/" in data["url"]
    finally:
        # Cleanup only the overrides we added (preserve CSRF mock from conftest)
        app.dependency_overrides.pop(get_storage_service, None)
        app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.asyncio
async def test_api_get_presigned_url(client, storage_service):
    app.dependency_overrides[get_storage_service] = lambda: storage_service
    
    try:
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
        assert "/api/storage/m/" in data["url"]
        assert "signature=" in data["url"]
    finally:
        # Cleanup only the overrides we added (preserve CSRF mock from conftest)
        from src.dependencies import get_current_user
        app.dependency_overrides.pop(get_storage_service, None)
        app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.asyncio
async def test_api_get_bulk_presigned_urls(client, storage_service):
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
    
    try:
        filenames = ["journal/user123/img.jpg", "ticket/user123/img.png"]
        response = await client.post("/api/storage/presign/bulk", json={"filenames": filenames})
        
        assert response.status_code == 200
        data = response.json()
        assert "urls" in data
        assert len(data["urls"]) == 2
        assert "/api/storage/m/journal/user123/img.jpg" in data["urls"]["journal/user123/img.jpg"]
        assert data["expires_in"] == 3600
    finally:
        app.dependency_overrides.pop(get_storage_service, None)
        app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.asyncio
async def test_get_external_media_cache_hit(storage_service):
    path = "media/jkt48-member/shani.jpg"
    
    # Mock cache hit
    storage_service.repository.get_file_stream_with_metadata.return_value = (io.BytesIO(b"cached_content"), "image/jpeg")
    
    stream, media_type, status = await storage_service.get_external_media(path)
    
    assert status == 200
    assert stream.read() == b"cached_content"
    assert media_type == "image/jpeg"
    storage_service.repository.get_file_stream_with_metadata.assert_called_with("cache/external/media/jkt48-member/shani.jpg")

@pytest.mark.asyncio
async def test_get_external_media_cache_miss(storage_service, monkeypatch):
    path = "media/jkt48-member/new_member.jpg"
    
    # Mock cache miss (returns None)
    storage_service.repository.get_file_stream_with_metadata.return_value = (None, None)
    
    # Mock httpx.AsyncClient
    mock_client_instance = AsyncMock()
    
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.content = b"new_image_content"
            self.headers = {"content-type": "image/jpeg"}

    mock_client_instance.get.return_value = MockResponse()
    
    from unittest.mock import patch
    with patch("httpx.AsyncClient") as mock_client_class:
        # Patch the context manager: async with httpx.AsyncClient() as client
        mock_client_class.return_value.__aenter__.return_value = mock_client_instance
        
        content, media_type, status = await storage_service.get_external_media(path)
    
    assert status == 200
    assert content == b"new_image_content"
    # Verify it was cached
    storage_service.repository.upload_file.assert_called_with(
        b"new_image_content", "cache/external/media/jkt48-member/new_member.jpg", "image/jpeg"
    )

@pytest.mark.asyncio
async def test_api_proxy_external_media(client, storage_service):
    app.dependency_overrides[get_storage_service] = lambda: storage_service
    
    # Mock service response
    # StreamingResponse needs an iterable. io.BytesIO(b"...") is an iterable but yields bytes one by one? 
    # Actually for StreamingResponse, a list of bytes [b"..."] or a generator is better in tests.
    storage_service.get_external_media = AsyncMock(return_value=([b"image_data"], "image/png", 200))
    
    try:
        response = await client.get("/api/storage/external/member/1.png")
        assert response.status_code == 200
        assert response.content == b"image_data"
        assert response.headers["content-type"] == "image/png"
        assert "Cache-Control" in response.headers
    finally:
        app.dependency_overrides.pop(get_storage_service, None)


@pytest.mark.asyncio
async def test_api_proxy_internal_media(client, storage_service):
    """
    Test the actual /storage/m/{path} endpoint that verifies signatures.
    """
    app.dependency_overrides[get_storage_service] = lambda: storage_service
    
    path = "tickets/u1/evidence.png"
    
    # 1. Generate valid params using the service's internal logic
    signature, expires = storage_service._create_signed_params(path)
    
    try:
        # 2. Test Success (Valid Signature)
        response = await client.get(f"/api/storage/m/{path}?expires={expires}&signature={signature}")
        assert response.status_code == 200
        assert response.content == b"fake_image_content"
        assert response.headers["X-Robots-Tag"] == "noindex, nofollow, noarchive"
        
        # 3. Test Failure (Invalid Signature)
        bad_sig = "invalid_signature"
        response = await client.get(f"/api/storage/m/{path}?expires={expires}&signature={bad_sig}")
        assert response.status_code == 401
        assert "Unauthorized" in response.text
        
        # 4. Test Failure (Expired)
        expired_time = 1000000000 # Way in the past
        expired_sig = storage_service._generate_signature(path, expired_time)
        response = await client.get(f"/api/storage/m/{path}?expires={expired_time}&signature={expired_sig}")
        assert response.status_code == 401
        assert "expired" in response.text.lower()

    finally:
        app.dependency_overrides.pop(get_storage_service, None)
