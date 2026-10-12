import asyncio
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config
from src.database import database_instance

# Page48 notifications older than this are deleted by MongoDB itself.
NOTIFICATION_TTL_DAYS = 30


async def create_indexes():
    """Create database indexes."""
    try:
        db = database_instance.database

        # Users indexes
        await db["users"].create_index("userId", unique=True)
        await db["users"].create_index("username", unique=True)
        await db["users"].create_index("email", unique=True)
        # Locked Page48 accounts are looked up on every Page48 read; the partial
        # filter keeps this index tiny when nobody has locked their account.
        await db["users"].create_index(
            [("page48Locked", 1)], partialFilterExpression={"page48Locked": True}
        )

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

        # Page48 indexes
        await db["page48_posts"].create_index([("createdAt", -1)])
        await db["page48_posts"].create_index("postId", unique=True)
        await db["page48_posts"].create_index([("userId", 1), ("parentPostId", 1), ("createdAt", -1)])
        await db["page48_posts"].create_index([("rootPostId", 1), ("createdAt", 1)])
        await db["page48_posts"].create_index([("parentPostId", 1), ("createdAt", 1)])
        await db["page48_posts"].create_index("tags")
        # Search: free words match token prefixes, and `@` matches mentions.
        await db["page48_posts"].create_index("searchTokens")
        await db["page48_posts"].create_index("mentions")
        await db["page48_posts"].create_index([("quotedPostId", 1), ("createdAt", -1)])
        await db["page48_posts"].create_index("quotedPostId")
        await db["page48_posts"].create_index([("userId", 1), ("pinnedAt", -1)])

        await db["page48_likes"].create_index([("postId", 1), ("userId", 1)], unique=True)
        await db["page48_likes"].create_index([("userId", 1), ("createdAt", -1)])
        await db["page48_likes"].create_index([("postId", 1), ("createdAt", -1)])

        await db["page48_bookmarks"].create_index([("postId", 1), ("userId", 1)], unique=True)
        await db["page48_bookmarks"].create_index([("userId", 1), ("createdAt", -1)])

        await db["page48_reposts"].create_index([("postId", 1), ("userId", 1)], unique=True)
        await db["page48_reposts"].create_index([("userId", 1), ("createdAt", -1)])
        await db["page48_reposts"].create_index([("postId", 1), ("createdAt", -1)])

        await db["page48_reports"].create_index([("status", 1), ("createdAt", -1)])
        await db["page48_reports"].create_index(
            [("reporterUserId", 1), ("targetType", 1), ("targetId", 1)], unique=True
        )

        # Blocks and mutes. A block is checked in both directions, so the reverse
        # pair is indexed too; a mute is only ever read one way.
        await db["page48_blocks"].create_index(
            [("blockerId", 1), ("blockedId", 1)], unique=True
        )
        await db["page48_blocks"].create_index([("blockedId", 1), ("blockerId", 1)])
        await db["page48_blocks"].create_index([("blockerId", 1), ("createdAt", -1)])
        await db["page48_mutes"].create_index(
            [("muterId", 1), ("mutedId", 1)], unique=True
        )
        await db["page48_mutes"].create_index([("muterId", 1), ("createdAt", -1)])

        # Notifications: newest first per recipient for the list, plus the unread
        # count. They expire on their own so the collection cannot grow forever.
        await db["page48_notifications"].create_index("notificationId", unique=True)
        await db["page48_notifications"].create_index(
            [("recipientUserId", 1), ("createdAt", -1), ("notificationId", -1)]
        )
        await db["page48_notifications"].create_index(
            [("recipientUserId", 1), ("readAt", 1)]
        )
        # The per-tab list filters on the type, so it gets its own index instead of
        # scanning every entry of the recipient's newest-first index.
        await db["page48_notifications"].create_index(
            [
                ("recipientUserId", 1),
                ("type", 1),
                ("createdAt", -1),
                ("notificationId", -1),
            ]
        )
        # Only like/repost/follow carry a dedupe key, so the index is sparse: the
        # repeatable types keep one row, while replies and mentions stay a log.
        await db["page48_notifications"].create_index(
            "dedupeKey", unique=True, sparse=True
        )
        await db["page48_notifications"].create_index(
            "createdAt", expireAfterSeconds=NOTIFICATION_TTL_DAYS * 24 * 60 * 60
        )

        # Poll votes: the unique key is what guarantees one vote per user, and the
        # (postId, optionId) index backs the per-option counting aggregation.
        await db["page48_poll_votes"].create_index(
            [("postId", 1), ("userId", 1)], unique=True
        )
        await db["page48_poll_votes"].create_index([("postId", 1), ("optionId", 1)])
        await db["page48_poll_votes"].create_index([("userId", 1), ("createdAt", -1)])

        # Follow edges: the unique pair prevents double follows, the two compound
        # indexes back the followers/following lists and their live counts.
        await db["page48_follows"].create_index(
            [("followerId", 1), ("followingId", 1)], unique=True
        )
        await db["page48_follows"].create_index([("followerId", 1), ("createdAt", -1)])
        await db["page48_follows"].create_index([("followingId", 1), ("createdAt", -1)])
        # Pending requests are read straight off the Follows tab of a locked account.
        await db["page48_follows"].create_index(
            [("followingId", 1), ("status", 1), ("createdAt", -1)]
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
