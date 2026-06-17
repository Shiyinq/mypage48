import asyncio
import os
import sys
import httpx
from io import BytesIO
from urllib.parse import urlparse

from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Settings
from src.logging_config import create_logger
from src.storage.repository import StorageRepository
from src.storage.service import StorageService

logger = create_logger("migrate_live_history", __name__)

async def process_live_history(db, storage_service, storage_repo):
    col = db["live_history"]
    logger.info("Fetching lives to migrate...")
    # Find records with an image that is not null, not internal, and not empty
    query = {"image": {"$exists": True, "$ne": None, "$nin": ["", "-"]}}
    cursor = col.find(query)
    
    lives = await cursor.to_list(length=None)
    migrated_count = 0
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        for live in lives:
            image_url = live.get("image")
            if not image_url or image_url.startswith("live/"):
                continue
            
            logger.info(f"Migrating image for live {live.get('live_id')}: {image_url}")
            try:
                resp = await client.get(image_url)
                if resp.status_code == 200:
                    parsed_url = urlparse(image_url)
                    base_name = os.path.basename(parsed_url.path)
                    name_without_ext = os.path.splitext(base_name)[0]
                    filename = f"live/{name_without_ext}.webp"
                    
                    img = Image.open(BytesIO(resp.content))
                    if img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGBA")
                    else:
                        img = img.convert("RGB")
                    
                    blurHash = storage_service._generate_blurhash_from_image(img)
                    
                    output = BytesIO()
                    img.save(output, format="WEBP", quality=storage_service.WEBP_QUALITY)
                    webp_bytes = output.getvalue()
                    
                    await storage_service._generate_and_upload_variants(img, filename)
                    metadata = {"blurHash": blurHash} if blurHash else None
                    await storage_repo.upload_file(webp_bytes, filename, "image/webp", metadata=metadata)
                    
                    new_path = filename
                    update_data = {"image": new_path}
                    if blurHash:
                        update_data["blurHash"] = blurHash
                    
                    await col.update_one({"_id": live["_id"]}, {"$set": update_data})
                    logger.info(f"Successfully migrated to {new_path}")
                    migrated_count += 1
                else:
                    logger.warning(f"Failed to fetch {image_url}, status code: {resp.status_code}")
            except Exception as e:
                logger.error(f"Error migrating {image_url}: {str(e)}")
                
    logger.info(f"Migration completed! Migrated {migrated_count} images.")

async def main():
    settings = Settings()
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.db_name]

    storage_repo = StorageRepository(settings)
    storage_service = StorageService(storage_repo, settings)

    await process_live_history(db, storage_service, storage_repo)
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
