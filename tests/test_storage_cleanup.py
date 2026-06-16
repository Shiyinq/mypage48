import pytest
from unittest.mock import AsyncMock, MagicMock
from src.storage.service import StorageService
from src.config import Settings

@pytest.mark.asyncio
async def test_delete_image_with_variants():
    # Mock repository
    repo = AsyncMock()
    repo.file_exists.return_value = True
    repo.delete_file.return_value = True
    
    # Mock config
    config = MagicMock(spec=Settings)
    
    service = StorageService(repo, config)
    
    filename = "ticket/user123/test_image.webp"
    success = await service.delete_image(filename)
    
    assert success is True
    
    # Verify calls
    expected_calls = [
        "ticket/user123/test_image.webp",
        "ticket/user123/test_image_medium.webp",
        "ticket/user123/test_image_small.webp"
    ]
    
    called_paths = [call.args[0] for call in repo.delete_file.call_args_list]
    
    for path in expected_calls:
        assert path in called_paths, f"{path} was NOT deleted"

@pytest.mark.asyncio
async def test_skip_external_urls():
    repo = AsyncMock()
    config = MagicMock(spec=Settings)
    service = StorageService(repo, config)
    
    urls = [
        "https://jkt48.com/images/member/test.jpg",
        "http://example.com/image.png",
        "data:image/png;base64,xxxx"
    ]
    
    for url in urls:
        success = await service.delete_image(url)
        # Should return False because it skipped deletion for non-internal path
        assert success is False
        assert repo.delete_file.call_count == 0, f"Failed to skip: {url}"
