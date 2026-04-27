import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.storage.service import StorageService
from src.config import Settings

async def test_delete_image_with_variants():
    print("Testing delete_image with variants...")
    
    # Mock repository
    repo = AsyncMock()
    repo.file_exists.return_value = True
    repo.delete_file.return_value = True
    
    # Mock config
    config = MagicMock(spec=Settings)
    
    service = StorageService(repo, config)
    
    filename = "ticket/user123/test_image.webp"
    success = await service.delete_image(filename)
    
    print(f"Delete success: {success}")
    
    # Verify calls
    expected_calls = [
        "ticket/user123/test_image.webp",
        "ticket/user123/test_image_medium.webp",
        "ticket/user123/test_image_small.webp"
    ]
    
    called_paths = [call.args[0] for call in repo.delete_file.call_args_list]
    print(f"Deleted paths: {called_paths}")
    
    for path in expected_calls:
        if path in called_paths:
            print(f"✓ {path} was deleted")
        else:
            print(f"✗ {path} was NOT deleted")
            return False
            
    return True

async def test_skip_external_urls():
    print("\nTesting skip deletion for external URLs...")
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
        if not success and repo.delete_file.call_count == 0:
            print(f"✓ Correctly skipped: {url[:30]}...")
        else:
            print(f"✗ Failed to skip: {url}")
            return False
    return True

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    s1 = loop.run_until_complete(test_delete_image_with_variants())
    s2 = loop.run_until_complete(test_skip_external_urls())
    
    if s1 and s2:
        print("\nALL STORAGE TESTS PASSED")
        sys.exit(0)
    else:
        print("\nSOME TESTS FAILED")
        sys.exit(1)
