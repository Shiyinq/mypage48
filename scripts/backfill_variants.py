import asyncio
import os
import sys
from io import BytesIO

from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image

# Add the project root to sys.path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Settings
from src.logging_config import create_logger
from src.storage.repository import StorageRepository
from src.storage.service import StorageService

# Use a clean logger
logger = create_logger("backfill_variants", __name__)


async def process_image(
    storage_service: StorageService, path: str, is_external: bool = False
):
    """Generate variants for a single image if they don't exist."""
    if not path or path == "-":
        return

    # Standardize path
    path = path.lstrip("/")
    
    # Skip if path looks like base64 data or is suspiciously long (URI Too Long protection)
    if len(path) > 1000 or path.startswith("data:"):
        # logger.warning(f"Skipping invalid path (too long or base64): {path[:50]}...")
        return

    # For external media, we need to check the cache path
    storage_path = f"cache/external/{path}" if is_external else path

    # Check if variants already exist
    medium_path = storage_service._get_variant_path(storage_path, "medium")
    small_path = storage_service._get_variant_path(storage_path, "small")

    if await storage_service.repository.file_exists(
        medium_path
    ) and await storage_service.repository.file_exists(small_path):
        # logger.debug(f"Variants already exist for {path}")
        return

    logger.info(
        f"Generating variants for {path} ({'external' if is_external else 'internal'})..."
    )

    try:
        # Get original image bytes
        img_bytes = None
        if is_external:
            # Check cache first
            img_bytes = await storage_service.repository.get_file(storage_path)
            if not img_bytes:
                # Need to download and cache original first
                # _cache_external_media does this AND generates variants
                logger.info(f"Original for {path} not in cache, fetching...")
                await storage_service._cache_external_media(path)
                return
        else:
            img_bytes = await storage_service.repository.get_file(storage_path)

        if not img_bytes:
            logger.error(f"Could not find original image: {storage_path}")
            return

        # Generate variants
        with Image.open(BytesIO(img_bytes)) as img:
            # Convert to RGB if necessary (WEBP standard)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Note: Using the private helper method from StorageService
            # This is acceptable for a maintenance script
            await storage_service._generate_and_upload_variants(img, storage_path)
            logger.info(f"Successfully generated variants for {path}")

    except Exception as e:
        logger.error(f"Failed to process {path}: {e}")


async def main():
    settings = Settings()
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.db_name]

    storage_repo = StorageRepository(settings)
    storage_service = StorageService(storage_repo, settings)

    logger.info("Starting Backfill Variants process...")

    # 1. Members (External)
    members_col = db["members"]
    logger.info("Gathering active members...")
    members = await members_col.find({"img": {"$ne": None, "$ne": "-"}}).to_list(
        length=None
    )
    logger.info(f"Found {len(members)} members to check.")
    for member in members:
        await process_image(storage_service, member["img"], is_external=True)

    # 2. Tickets & 2-Shot (Internal)
    tickets_col = db["tickets"]
    logger.info("Gathering tickets...")
    tickets = await tickets_col.find(
        {
            "$or": [
                {"imageUrl": {"$ne": None}},
                {"two_shot.imageUrl": {"$ne": None}},
            ]
        }
    ).to_list(length=None)
    logger.info(f"Found {len(tickets)} tickets to check.")

    for ticket in tickets:
        # Main image
        if ticket.get("imageUrl"):
            await process_image(storage_service, ticket["imageUrl"])

        # 2-Shot image
        if ticket.get("two_shot") and ticket["two_shot"].get("imageUrl"):
            await process_image(storage_service, ticket["two_shot"]["imageUrl"])

    logger.info("Backfill Variants process completed!")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
