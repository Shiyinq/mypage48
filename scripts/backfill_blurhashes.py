import asyncio
import os
import sys
from io import BytesIO

import blurhash
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image

# Add the project root to sys.path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Settings
from src.logging_config import create_logger

# Use a clean logger
logger = create_logger("backfill_blurhashes", __name__)


def generate_blurhash(image_bytes: bytes) -> str:
    """Generate a BlurHash for the given image bytes."""
    with Image.open(BytesIO(image_bytes)) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((32, 32))
        width, height = img.size
        x_components = 4
        y_components = 4 if height >= width else 3
        return blurhash.encode(
            img, x_components=x_components, y_components=y_components
        )


async def download_image(url: str) -> bytes:
    """Download image from URL."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def process_tickets(db, storage_resolver):
    """Backfill BlurHashes for tickets."""
    collection = db["tickets"]
    query = {"$or": [
        {"imageUrl": {"$exists": True, "$ne": None}, "blurHash": {"$exists": False}},
        {"two_shot.imageUrl": {"$exists": True, "$ne": None}, "two_shot.blurHash": {"$exists": False}}
    ]}
    
    count = await collection.count_documents(query)
    logger.info(f"Found {count} tickets to process")
    
    cursor = collection.find(query)
    async for ticket in cursor:
        updates = {}
        
        # Process main image
        if ticket.get("imageUrl") and not ticket.get("blurHash"):
            try:
                url = await storage_resolver(ticket["imageUrl"])
                logger.info(f"Processing ticket {ticket['_id']} main image...")
                img_bytes = await download_image(url)
                updates["blurHash"] = generate_blurhash(img_bytes)
            except Exception as e:
                logger.error(f"Failed to process ticket {ticket['_id']} main image: {e}")

        # Process two_shot image
        if ticket.get("two_shot") and ticket["two_shot"].get("imageUrl") and not ticket["two_shot"].get("blurHash"):
            try:
                url = await storage_resolver(ticket["two_shot"]["imageUrl"])
                logger.info(f"Processing ticket {ticket['_id']} 2-shot image...")
                img_bytes = await download_image(url)
                updates["two_shot.blurHash"] = generate_blurhash(img_bytes)
            except Exception as e:
                logger.error(f"Failed to process ticket {ticket['_id']} 2-shot image: {e}")
        
        if updates:
            await collection.update_one({"_id": ticket["_id"]}, {"$set": updates})
            logger.info(f"Updated ticket {ticket['_id']}")


async def process_members(db, storage_resolver):
    """Backfill BlurHashes for members."""
    collection = db["members"]
    query = {"img": {"$exists": True, "$ne": None, "$ne": "-"}, "blurHash": {"$exists": False}}
    
    count = await collection.count_documents(query)
    logger.info(f"Found {count} members to process")
    
    cursor = collection.find(query)
    async for member in cursor:
        if member.get("img"):
            try:
                # Handle potential external URL resolve if needed
                # For members, resolve_external_url usually handles this
                url = await storage_resolver(member["img"])
                logger.info(f"Processing member {member['name']}...")
                img_bytes = await download_image(url)
                bh = generate_blurhash(img_bytes)
                await collection.update_one({"_id": member["_id"]}, {"$set": {"blurHash": bh}})
                logger.info(f"Updated member {member['name']}")
            except Exception as e:
                logger.error(f"Failed to process member {member.get('name')}: {e}")


async def process_news(db, storage_resolver):
    """Backfill BlurHashes for news."""
    collection = db["news"]
    query = {"background_image": {"$exists": True, "$ne": None}, "blurHash": {"$exists": False}}
    
    count = await collection.count_documents(query)
    logger.info(f"Found {count} news items to process")
    
    cursor = collection.find(query)
    async for news in cursor:
        if news.get("background_image"):
            try:
                url = await storage_resolver(news["background_image"])
                logger.info(f"Processing news {news['news_id']}...")
                img_bytes = await download_image(url)
                bh = generate_blurhash(img_bytes)
                await collection.update_one({"_id": news["_id"]}, {"$set": {"blurHash": bh}})
                logger.info(f"Updated news {news['news_id']}")
            except Exception as e:
                logger.error(f"Failed to process news {news.get('news_id')}: {e}")


async def main():
    settings = Settings()
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.db_name]
    
    # Initialize storage service for URL resolution
    from src.storage.repository import StorageRepository
    from src.storage.service import StorageService
    
    storage_repo = StorageRepository(settings)
    storage_service = StorageService(storage_repo, settings)
    
    logger.info("Starting backfill process...")
    
    # 1. Tickets (Internal images)
    await process_tickets(db, storage_service.resolve_url)
    
    # 2. Members (External images)
    await process_members(db, storage_service.resolve_external_url)
    
    # 3. News (External images)
    # await process_news(db, storage_service.resolve_external_url)
    
    logger.info("Backfill process completed!")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
