import asyncio
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config
from src.database import database_instance

async def create_indexes():
    """Create database indexes."""
    try:
        db = database_instance.database

        # Users indexes
        await db["users"].create_index("userId", unique=True)
        await db["users"].create_index("username", unique=True)
        await db["users"].create_index("email", unique=True)

        # Refresh token indexes
        await db["refresh_tokens"].create_index("hashRefreshToken", unique=True)
        await db["refresh_tokens"].create_index("userId")
        
        expire_seconds = config.refresh_token_max_age_days * 24 * 60 * 60
        await db["refresh_tokens"].create_index(
            "createdAt", expireAfterSeconds=expire_seconds
        )

        # API keys indexes
        await db["api_keys"].create_index("userId")

        # Verification tokens indexes
        await db["verification_tokens"].create_index("userId")
        await db["verification_tokens"].create_index("hashToken", unique=True)
        await db["verification_tokens"].create_index("expiresAt", expireAfterSeconds=0)

        # Members indexes (Only ID, Name, Nickname)
        await db["members"].create_index("id", unique=True)
        await db["members"].create_index("name")
        await db["members"].create_index("nickname")

        # Tickets indexes
        await db["tickets"].create_index("ticket_id")
        await db["tickets"].create_index("user_id")
        await db["tickets"].create_index("event.venue")
        await db["tickets"].create_index("event.date")
        await db["tickets"].create_index("event.time")
        await db["tickets"].create_index("event.title")
        await db["tickets"].create_index("two_shot.member_name")
        
        # Compound index for fast filtering and sorting in history page
        await db["tickets"].create_index([
            ("user_id", 1), 
            ("event.date", -1), 
            ("event.time", -1)
        ])

        # Replay indexes
        await db["replay"].create_index("platform")
        await db["replay"].create_index("live_id", unique=True)
        await db["replay"].create_index([("recording_ended_at", -1)])
        await db["replay"].create_index("youtube_id", sparse=True)

        await db["replay"].create_index(
            [("recording_ended_at", -1)],
            name="partial_recording_ended_at_-1_youtube",
            partialFilterExpression={"youtube_id": {"$gt": ""}}
        )
        
        await db["replay"].create_index(
            [("platform", 1), ("recording_ended_at", -1)],
            name="partial_platform_-1_youtube",
            collation={"locale": "en", "strength": 2},
            partialFilterExpression={"youtube_id": {"$gt": ""}}
        )

        await db["replay"].create_index(
            [("member_nickname", 1), ("recording_ended_at", -1)],
            name="partial_member_-1_youtube",
            collation={"locale": "en", "strength": 2},
            partialFilterExpression={"youtube_id": {"$gt": ""}}
        )

        # Replay Chats indexes
        await db["replay_chats"].create_index("live_id", unique=True)

        # Live history indexes
        await db["live_history"].create_index("platform")
        await db["live_history"].create_index([("start_at", -1)])
        await db["live_history"].create_index("live_id")
        await db["live_history"].create_index("member.id")

        # Watched live history indexes
        await db["watched_live_history"].create_index([("user_id", 1), ("started_at", -1)])
        await db["watched_live_history"].create_index([("live_id", 1)])
        await db["watched_live_history"].create_index(
            [("user_id", 1), ("member_id", 1), ("started_at", -1)]
        )

        print("Database indexes created successfully")
    except Exception as e:
        print(f"Failed to create indexes: {str(e)}")
        raise e

async def main():
    print("Initializing database connection...")
    
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            await database_instance.connect()
            await database_instance.database.command("ping")
            print("Successfully connected to MongoDB!")
            break
        except Exception as e:
            print(f"Waiting for database... (Attempt {i+1}/{max_retries}) Error: {e}")
            if i < max_retries - 1:
                await asyncio.sleep(retry_interval)
            else:
                print("Could not connect to database after multiple attempts.")
                sys.exit(1)

    try:
        print("Creating database indexes...")
        await create_indexes()
    except Exception as e:
        print(f"Error process: {e}")
        # Exit with error code 1 to signal failure to CI/CD
        sys.exit(1)
    finally:
        print("Closing database connection...")
        await database_instance.close()

if __name__ == "__main__":
    asyncio.run(main())
