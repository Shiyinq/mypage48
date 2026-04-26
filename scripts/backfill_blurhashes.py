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


def is_valid_blurhash(bh: str) -> bool:
    """Check if the given string is a potentially valid BlurHash."""
    if not bh:
        return False
    # If it contains MIME encoding format, it's invalid for our frontend
    if "=?utf-8?Q?" in bh:
        return False
    # Simple length check (BlurHash is usually > 10 chars)
    return len(bh) > 5


async def process_tickets(db, storage_service):
    """Backfill BlurHashes for tickets."""
    collection = db["tickets"]
    # Update query to include records where blurHash is missing, null, or invalid
    query = {"$or": [
        {"imageUrl": {"$exists": True, "$ne": None}, "$or": [{"blurHash": {"$exists": False}}, {"blurHash": None}, {"blurHash": {"$regex": "=\\?utf-8\\?Q\\?"}}]},
        {"two_shot.imageUrl": {"$exists": True, "$ne": None}, "$or": [{"two_shot.blurHash": {"$exists": False}}, {"two_shot.blurHash": None}, {"two_shot.blurHash": {"$regex": "=\\?utf-8\\?Q\\?"}}]}
    ]}
    
    count = await collection.count_documents(query)
    logger.info(f"Found {count} tickets to process")
    
    cursor = collection.find(query)
    async for ticket in cursor:
        updates = {}
        
        # Process main image
        if ticket.get("imageUrl") and not is_valid_blurhash(ticket.get("blurHash")):
            try:
                # Use resolve_image_variants as it now returns blurHash from S3 if available
                res = await storage_service.resolve_image_variants(ticket["imageUrl"])
                if is_valid_blurhash(res.get("blurHash")):
                    updates["blurHash"] = res["blurHash"]
                else:
                    url = res["url"]
                    logger.info(f"Processing ticket {ticket['_id']} main image (downloading)...")
                    img_bytes = await download_image(url)
                    updates["blurHash"] = generate_blurhash(img_bytes)
            except Exception as e:
                logger.error(f"Failed to process ticket {ticket['_id']} main image: {e}")

        # Process two_shot image
        if ticket.get("two_shot") and ticket["two_shot"].get("imageUrl") and not is_valid_blurhash(ticket["two_shot"].get("blurHash")):
            try:
                res = await storage_service.resolve_image_variants(ticket["two_shot"]["imageUrl"])
                if is_valid_blurhash(res.get("blurHash")):
                    updates["two_shot.blurHash"] = res["blurHash"]
                else:
                    url = res["url"]
                    logger.info(f"Processing ticket {ticket['_id']} 2-shot image (downloading)...")
                    img_bytes = await download_image(url)
                    updates["two_shot.blurHash"] = generate_blurhash(img_bytes)
            except Exception as e:
                logger.error(f"Failed to process ticket {ticket['_id']} 2-shot image: {e}")
        
        if updates:
            await collection.update_one({"_id": ticket["_id"]}, {"$set": updates})
            logger.info(f"Updated ticket {ticket['_id']}")


async def process_members(db, storage_service):
    """Backfill BlurHashes for members."""
    collection = db["members"]
    query = {"img": {"$exists": True, "$ne": None, "$ne": "-"}, "$or": [{"blurHash": {"$exists": False}}, {"blurHash": None}, {"blurHash": {"$regex": "=\\?utf-8\\?Q\\?"}}]}
    
    count = await collection.count_documents(query)
    logger.info(f"Found {count} members to process")
    
    cursor = collection.find(query)
    async for member in cursor:
        if member.get("img") and not is_valid_blurhash(member.get("blurHash")):
            try:
                # Try to resolve first (might be cached in S3 with metadata)
                img_path = member["img"]
                if img_path.startswith("media/") or "/" not in img_path:
                    res = await storage_service.resolve_image_variants(img_path)
                else:
                    res = await storage_service.resolve_external_media(img_path)
                
                if is_valid_blurhash(res.get("blurHash")):
                    bh = res["blurHash"]
                else:
                    logger.info(f"Processing member {member['name']} (downloading)...")
                    img_bytes = await download_image(res["url"])
                    bh = generate_blurhash(img_bytes)
                
                await collection.update_one({"_id": member["_id"]}, {"$set": {"blurHash": bh}})
                logger.info(f"Updated member {member['name']}")
            except Exception as e:
                logger.error(f"Failed to process member {member.get('name')}: {e}")


async def process_setlists(db, storage_service):
    """Backfill BlurHashes for setlists."""
    collection = db["setlists"]
    query = {"imageUrl": {"$exists": True, "$ne": None}, "$or": [{"blurHash": {"$exists": False}}, {"blurHash": None}, {"blurHash": {"$regex": "=\\?utf-8\\?Q\\?"}}]}
    
    count = await collection.count_documents(query)
    logger.info(f"Found {count} setlists to process")
    
    cursor = collection.find(query)
    async for setlist in cursor:
        if setlist.get("imageUrl") and not is_valid_blurhash(setlist.get("blurHash")):
            try:
                res = await storage_service.resolve_image_variants(setlist["imageUrl"])
                if is_valid_blurhash(res.get("blurHash")):
                    bh = res["blurHash"]
                else:
                    logger.info(f"Processing setlist {setlist['title']} (downloading)...")
                    img_bytes = await download_image(res["url"])
                    bh = generate_blurhash(img_bytes)
                
                await collection.update_one({"_id": setlist["_id"]}, {"$set": {"blurHash": bh}})
                logger.info(f"Updated setlist {setlist['title']}")
            except Exception as e:
                logger.error(f"Failed to process setlist {setlist.get('title')}: {e}")


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
    
    # 1. Tickets
    await process_tickets(db, storage_service)
    
    # 2. Members
    await process_members(db, storage_service)
    
    # 3. Setlists
    await process_setlists(db, storage_service)
    
    logger.info("Backfill process completed!")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
