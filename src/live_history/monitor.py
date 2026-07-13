import asyncio
import os
from io import BytesIO
from urllib.parse import urlparse

import httpx
from PIL import Image

from src.admin.repository import AdminRepository
from src.admin.service import AdminService
from src.config import config
from src.database import database_instance
from src.live.service import LiveService
from src.live_history.repository import LiveHistoryRepository
from src.logging_config import create_logger
from src.members.repository import MemberRepository
from src.storage.repository import StorageRepository
from src.storage.service import StorageService

logger = create_logger("live_history_monitor", __name__)


async def _process_new_live_image(
    client: httpx.AsyncClient,
    storage_service: StorageService,
    storage_repo: StorageRepository,
    image_url: str,
):
    """Download and process external live image, then upload to storage."""
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
            await storage_repo.upload_file(
                webp_bytes, filename, "image/webp", metadata=metadata
            )

            return filename, blurHash
    except Exception as e:
        logger.error(f"Failed to upload new live image {image_url}: {str(e)}")

    return None, None


async def live_monitor_loop():
    """Background task to poll live streams and maintain global history."""
    logger.info("Starting global live history monitor loop...")

    # Run indefinitely
    while True:
        try:
            db = database_instance.database
            member_repo = MemberRepository(db)
            admin_repo = AdminRepository(db)
            admin_service = AdminService(admin_repo)
            live_service = LiveService(member_repo, admin_service, config)
            live_history_repo = LiveHistoryRepository(db)

            storage_repo = StorageRepository(config)
            storage_service = StorageService(storage_repo, config)

            # Fetch active lives
            live_res = await live_service.get_live_status()
            current_lives = live_res.data

            current_live_ids = []

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                for live in current_lives:
                    live_dict = live.model_dump()
                    live_id = live_dict.get("live_id")
                    platform = live_dict.get("platform")

                    # Fallback to room_id if live_id is not present
                    unique_id = live_id if live_id else live_dict.get("room_id")

                    if unique_id:
                        current_live_ids.append(unique_id)

                        existing = await live_history_repo.history_col.find_one(
                            {"live_id": unique_id, "platform": platform}
                        )

                        if (
                            existing
                            and existing.get("image")
                            and existing["image"].startswith("live/")
                        ):
                            # Reuse existing internal image
                            live_dict["image"] = existing["image"]
                            live_dict["blurHash"] = existing.get("blurHash")
                        else:
                            # Try to download and upload if not internal
                            image_url = live_dict.get("image")
                            if image_url and not image_url.startswith("live/"):
                                new_path, blurHash = await _process_new_live_image(
                                    client, storage_service, storage_repo, image_url
                                )
                                if new_path:
                                    live_dict["image"] = new_path
                                if blurHash:
                                    live_dict["blurHash"] = blurHash

                        # Prepare for upsert
                        upsert_data = {
                            "live_id": unique_id,
                            "platform": platform,
                            "title": live_dict.get("title"),
                            "image": live_dict.get("image"),
                            "blurHash": live_dict.get("blurHash"),
                            "view_num": live_dict.get("view_num", 0),
                            "start_at": live_dict.get("start_at"),
                            "member": live_dict.get("member"),
                        }
                        await live_history_repo.upsert_global_live(upsert_data)

            # Mark missing lives as ended
            await live_history_repo.mark_missing_lives_as_ended(current_live_ids)

        except Exception as e:
            logger.error(f"Error in live monitor loop: {str(e)}")

        # Wait 1 minute before the next poll
        await asyncio.sleep(60)
