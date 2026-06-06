import asyncio

from src.live_history.repository import LiveHistoryRepository
from src.logging_config import create_logger

logger = create_logger("live_history_monitor", __name__)


async def live_monitor_loop():
    """Background task to poll live streams and maintain global history."""
    logger.info("Starting global live history monitor loop...")

    # Run indefinitely
    while True:
        try:
            # 1. Fetch current lives
            # We don't have dependency injection directly here, so we instantiate it manually or use a helper
            # Actually, get_live_service is a FastAPI dependency. Let's create instances manually.
            from src.database import database_instance
            from src.live.service import LiveService
            from src.members.repository import MemberRepository

            db = database_instance.database
            member_repo = MemberRepository(db)
            from src.config import config

            live_service = LiveService(member_repo, config)

            live_history_repo = LiveHistoryRepository(db)

            # Fetch active lives
            live_res = await live_service.get_live_status()
            current_lives = live_res.data

            current_live_ids = []

            for live in current_lives:
                # The LiveStatus model
                live_dict = live.model_dump()
                live_id = live_dict.get("live_id")
                platform = live_dict.get("platform")

                # If IDN uses live_id, but Showroom doesn't always have one initially, fallback to room_id
                unique_id = live_id if live_id else live_dict.get("room_id")

                if unique_id:
                    current_live_ids.append(unique_id)
                    # Prepare for upsert
                    upsert_data = {
                        "live_id": unique_id,
                        "platform": platform,
                        "title": live_dict.get("title"),
                        "image": live_dict.get("image"),
                        "view_num": live_dict.get("view_num", 0),
                        "start_at": live_dict.get("start_at"),
                        "member": live_dict.get("member"),
                    }
                    await live_history_repo.upsert_global_live(upsert_data)

            # 2. Mark missing lives as ended
            await live_history_repo.mark_missing_lives_as_ended(current_live_ids)

            # logger.debug(f"Live monitor poll completed. Found {len(current_live_ids)} active lives.")

        except Exception as e:
            logger.error(f"Error in live monitor loop: {e}")

        # Wait 1 minute before the next poll
        await asyncio.sleep(60)
