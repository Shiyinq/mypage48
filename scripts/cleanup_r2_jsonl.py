#!/usr/bin/env python3
"""Script to clean up legacy .jsonl chat files from Cloudflare R2 / MinIO storage
and clean up references in MongoDB replay documents.

Why this script exists:
- Raw chat messages are permanently stored in MongoDB (collection: 'replay_chats').
- Stream statistics (top gifts, top fans, total chats) are already precomputed in MongoDB ('replay').
- Frontend video player uses .srt subtitle files (via /api/replays/{live_id}/srt), never .jsonl.
- Storing .jsonl in R2 was redundant and takes unnecessary storage (~1.6MB+ per stream).

What this script does:
1. Scans storage under 'replay/' for any '*.jsonl' files.
2. Deletes those .jsonl files from R2/MinIO (frees storage).
3. Updates MongoDB 'replay' documents to set 'files.jsonl = None'.
   *Note*: Does NOT delete any chat records or statistics in MongoDB.

Usage:
    # 1. Local (Dry Run - preview only):
    .venv/bin/python scripts/cleanup_r2_jsonl.py

    # 2. Local (Apply deletion):
    .venv/bin/python scripts/cleanup_r2_jsonl.py --apply

    # 3. Production (via Docker backend container):
    docker exec -it mypage48-backend python /app/scripts/cleanup_r2_jsonl.py
    docker exec -it mypage48-backend python /app/scripts/cleanup_r2_jsonl.py --apply

    # 4. Production (if copying script into existing container without rebuild):
    docker cp scripts/cleanup_r2_jsonl.py mypage48-backend:/app/scripts/
    docker exec -it mypage48-backend python /app/scripts/cleanup_r2_jsonl.py --apply
"""

import argparse
import asyncio
import os
import sys

from minio import Minio
from minio.error import S3Error
from motor.motor_asyncio import AsyncIOMotorClient

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Settings
from src.logging_config import create_logger

logger = create_logger("cleanup_r2_jsonl", __name__)


async def cleanup_jsonl(apply_changes: bool = False):
    settings = Settings()

    # 1. Initialize MinIO / R2 Client
    endpoint = settings.storage_endpoint
    endpoint = endpoint.replace("https://", "").replace("http://", "").strip("/")

    client = Minio(
        endpoint,
        access_key=settings.storage_access_key,
        secret_key=settings.storage_secret_key,
        secure=settings.storage_secure,
    )
    bucket = settings.storage_bucket

    logger.info(f"Connecting to storage bucket: {bucket}")
    logger.info(
        f"Mode: {'APPLY (Actual deletion)' if apply_changes else 'DRY RUN (Preview only)'}"
    )

    # 2. Find .jsonl files in R2 storage under 'replay/'
    found_objects = []
    total_bytes = 0

    try:

        def _list_objects():
            return list(client.list_objects(bucket, prefix="replay/", recursive=True))

        objects = await asyncio.to_thread(_list_objects)
        for obj in objects:
            if not obj.is_dir and obj.object_name.endswith(".jsonl"):
                found_objects.append(obj)
                total_bytes += obj.size or 0
    except S3Error as e:
        logger.error(f"Error listing storage objects: {e}")
        return

    mb_size = total_bytes / (1024 * 1024)
    logger.info(f"Found {len(found_objects)} .jsonl file(s) in R2 ({mb_size:.2f} MB)")

    for obj in found_objects:
        size_kb = (obj.size or 0) / 1024
        logger.info(f"  - {obj.object_name} ({size_kb:.1f} KB)")

    # 3. Delete from R2 if apply_changes
    deleted_count = 0
    if apply_changes and found_objects:
        logger.info("Deleting .jsonl files from R2...")
        for obj in found_objects:
            try:

                def _remove(name=obj.object_name):
                    client.remove_object(bucket, name)

                await asyncio.to_thread(_remove)
                deleted_count += 1
                logger.info(f"  Deleted: {obj.object_name}")
            except Exception as e:
                logger.error(f"  Failed to delete {obj.object_name}: {e}")

        logger.info(
            f"Successfully deleted {deleted_count}/{len(found_objects)} files from R2."
        )
    elif not apply_changes and found_objects:
        logger.info(
            "Dry run complete. Use '--apply' to actually delete files from R2."
        )

    # 4. Clean up MongoDB references (files.jsonl -> None)
    logger.info("Checking MongoDB replay collection...")
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URI.get_secret_value())
    db = mongo_client[settings.DB_NAME]
    col_replay = db.replay

    query = {"files.jsonl": {"$exists": True, "$ne": None}}
    count_in_db = await col_replay.count_documents(query)
    logger.info(
        f"Found {count_in_db} replay record(s) in MongoDB with files.jsonl set."
    )

    if apply_changes and count_in_db > 0:
        res = await col_replay.update_many(query, {"$set": {"files.jsonl": None}})
        logger.info(
            f"Updated {res.modified_count} MongoDB replay record(s) (set files.jsonl = None)."
        )
    elif not apply_changes and count_in_db > 0:
        logger.info("Dry run complete. MongoDB records were not modified.")

    mongo_client.close()
    logger.info("Done!")


def main():
    parser = argparse.ArgumentParser(
        description="Clean up .jsonl chat files from R2 storage and MongoDB."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually perform the deletion. Defaults to dry-run.",
    )
    args = parser.parse_args()

    asyncio.run(cleanup_jsonl(apply_changes=args.apply))


if __name__ == "__main__":
    main()
