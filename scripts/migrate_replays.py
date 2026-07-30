import asyncio
import os
import sys

from motor.motor_asyncio import AsyncIOMotorClient

# Add src to python path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.config import config
from src.replay.service import _compute_chat_stats


async def main():
    client = AsyncIOMotorClient(config.mongo_uri)
    db = client[config.db_name]
    col_replay = db.replay
    col_chats = db.replay_chats

    # Ensure index on replay_chats
    await col_chats.create_index("live_id", unique=True)

    cursor = col_replay.find({"chats": {"$exists": True}})
    count = 0
    total = await col_replay.count_documents({"chats": {"$exists": True}})

    print(f"Found {total} replays with embedded chats to migrate.")

    async for doc in cursor:
        live_id = doc.get("live_id")
        chats = doc.get("chats", [])
        platform = doc.get("platform", "")

        if not live_id:
            continue

        print(f"Migrating {live_id} ({len(chats)} chats)...")

        # 1. Compute stats
        (
            top_gifts,
            top_fans,
            chat_count,
            gift_count,
            free_gift_count,
            total_gold,
            loveletter_count,
        ) = _compute_chat_stats(chats, platform)

        # 2. Insert into replay_chats
        try:
            await col_chats.update_one(
                {"live_id": live_id},
                {"$set": {"live_id": live_id, "chats": chats}},
                upsert=True,
            )
        except Exception as e:
            print(f"Failed to insert chats for {live_id}: {e}")
            continue

        # 3. Update replay document with stats and unset chats
        await col_replay.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "total_chats": chat_count,
                    "total_gifts": gift_count,
                    "total_free_gifts": free_gift_count,
                    "total_gold": total_gold,
                    "total_loveletters": loveletter_count,
                    "top_gifts": top_gifts,
                    "top_fans": top_fans,
                },
                "$unset": {"chats": ""},
            },
        )
        count += 1

    print(f"Migration complete! Processed {count} replays.")
    
    print("Compacting 'replay' collection to reclaim disk space...")
    try:
        await db.command("compact", "replay")
        print("Compaction complete. Storage size should now match data size.")
    except Exception as e:
        print(f"Failed to compact collection (this is normal if not running as admin/root): {e}")

if __name__ == "__main__":
    asyncio.run(main())
