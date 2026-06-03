import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.logging_config import create_logger


class LiveHistoryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.live_history
        self.logger = create_logger("live_history_repository", __name__)

    async def update_watch_duration(
        self,
        user_id: str,
        live_id: str,
        member_id: str,
        member_name: str,
        platform: str,
        ping_duration: int,
        member_nickname: Optional[str] = None,
        live_title: Optional[str] = None,
    ) -> bool:
        try:
            now = datetime.datetime.now(datetime.timezone.utc)

            set_fields = {"last_updated_at": now, "member_name": member_name}
            if member_nickname:
                set_fields["member_nickname"] = member_nickname
            if live_title:
                set_fields["live_title"] = live_title

            result = await self.collection.update_one(
                {
                    "user_id": user_id,
                    "live_id": live_id,
                    "member_id": member_id,
                    "platform": platform,
                },
                {
                    "$inc": {"duration": ping_duration},
                    "$set": set_fields,
                    "$setOnInsert": {"started_at": now},
                },
                upsert=True,
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to update live history: {e}")
            return False

    async def get_history_by_user(
        self, user_id: str, skip: int = 0, limit: int = 20
    ) -> List[Dict[str, Any]]:
        cursor = (
            self.collection.find({"user_id": user_id})
            .sort("last_updated_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def get_history_by_user_and_member(
        self, user_id: str, member_id: str, skip: int = 0, limit: int = 20
    ) -> List[Dict[str, Any]]:
        cursor = (
            self.collection.find({"user_id": user_id, "member_id": member_id})
            .sort("last_updated_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def get_total_history_count(
        self, user_id: str, member_id: Optional[str] = None
    ) -> int:
        query = {"user_id": user_id}
        if member_id:
            query["member_id"] = member_id
        return await self.collection.count_documents(query)

    async def get_overall_stats(self, user_id: str) -> Dict[str, Any]:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": "$member_id",
                    "member_name": {"$first": "$member_name"},
                    "total_duration": {"$sum": "$duration"},
                    "watch_count": {"$sum": 1},
                }
            },
        ]
        cursor = self.collection.aggregate(pipeline)

        total_duration = 0
        total_watches = 0
        top_member_id = None
        top_member_name = None
        top_member_watches = 0

        member_counts = {}
        member_durations = {}

        async for doc in cursor:
            member_id = doc["_id"]
            dur = doc["total_duration"]
            watches = doc["watch_count"]
            m_name = doc.get("member_name")

            total_duration += dur
            total_watches += watches

            member_counts[member_id] = watches
            member_durations[member_id] = dur

            if watches > top_member_watches:
                top_member_watches = watches
                top_member_id = member_id
                top_member_name = m_name

        platform_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        ]
        platform_cursor = self.collection.aggregate(platform_pipeline)
        platform_counts = {doc["_id"]: doc["count"] async for doc in platform_cursor}

        return {
            "total_duration": total_duration,
            "total_watches": total_watches,
            "top_member_id": top_member_id,
            "top_member_name": top_member_name,
            "top_member_watches": top_member_watches,
            "member_counts": member_counts,
            "member_durations": member_durations,
            "platform_counts": platform_counts,
        }

    async def get_longest_watch(
        self, user_id: str, member_id: str = None
    ) -> Optional[Dict[str, Any]]:
        query = {"user_id": user_id}
        if member_id:
            query["member_id"] = member_id

        longest_doc = await self.collection.find_one(query, sort=[("duration", -1)])

        if not longest_doc:
            return None

        return {
            "duration": longest_doc["duration"],
            "live_title": longest_doc.get("live_title"),
            "platform": longest_doc.get("platform"),
            "started_at": longest_doc.get("started_at"),
            "member_name": longest_doc.get("member_name"),
        }

    async def get_member_stats(self, user_id: str, member_id: str) -> Dict[str, Any]:
        pipeline = [
            {"$match": {"user_id": user_id, "member_id": member_id}},
            {
                "$group": {
                    "_id": None,
                    "total_duration": {"$sum": "$duration"},
                    "total_watches": {"$sum": 1},
                }
            },
        ]
        cursor = self.collection.aggregate(pipeline)
        results = [doc async for doc in cursor]

        if not results:
            return {
                "member_id": member_id,
                "total_duration": 0,
                "total_watches": 0,
                "platform_counts": {},
                "longest_watch": None,
            }

        longest_watch = await self.get_longest_watch(user_id, member_id)

        platform_pipeline = [
            {"$match": {"user_id": user_id, "member_id": member_id}},
            {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        ]
        platform_cursor = self.collection.aggregate(platform_pipeline)
        platform_counts = {doc["_id"]: doc["count"] async for doc in platform_cursor}

        return {
            "member_id": member_id,
            "total_duration": results[0]["total_duration"],
            "total_watches": results[0]["total_watches"],
            "platform_counts": platform_counts,
            "longest_watch": longest_watch,
        }

    async def upsert_global_live(self, live_data: Dict[str, Any]) -> None:
        """Upsert a live stream into the global history."""
        try:
            live_id = live_data["live_id"]
            platform = live_data["platform"]

            # Find existing
            existing = await self.db.global_live_history.find_one(
                {"live_id": live_id, "platform": platform}
            )
            now = datetime.datetime.now(datetime.timezone.utc)

            if existing:
                # Update max view_num
                view_num = max(
                    existing.get("view_num", 0), live_data.get("view_num", 0)
                )
                await self.db.global_live_history.update_one(
                    {"_id": existing["_id"]},
                    {
                        "$set": {
                            "view_num": view_num,
                            "last_seen_at": now,
                            "title": live_data.get("title"),
                            "image": live_data.get("image"),
                            "status": "live",
                        }
                    },
                )
            else:
                # Insert new
                live_data["last_seen_at"] = now
                live_data["status"] = "live"
                if not live_data.get("start_at"):
                    live_data["start_at"] = now
                await self.db.global_live_history.insert_one(live_data)
        except Exception as e:
            self.logger.error(f"Failed to upsert global live: {e}")

    async def mark_missing_lives_as_ended(self, current_live_ids: List[str]) -> None:
        """Mark lives that are currently 'live' but not in current_live_ids as 'ended'."""
        try:
            # Find all lives currently marked as 'live'
            cursor = self.db.global_live_history.find({"status": "live"})
            async for doc in cursor:
                live_id = doc.get("live_id")
                if live_id not in current_live_ids:
                    # Calculate duration
                    start_at = doc.get("start_at")
                    last_seen_at = doc.get("last_seen_at")
                    duration = 0
                    if start_at and last_seen_at:
                        # Ensure both are offset-aware for subtraction
                        if start_at.tzinfo is None:
                            start_at = start_at.replace(tzinfo=datetime.timezone.utc)
                        if last_seen_at.tzinfo is None:
                            last_seen_at = last_seen_at.replace(
                                tzinfo=datetime.timezone.utc
                            )
                        duration = int((last_seen_at - start_at).total_seconds())

                    await self.db.global_live_history.update_one(
                        {"_id": doc["_id"]},
                        {
                            "$set": {
                                "status": "ended",
                                "end_at": last_seen_at,
                                "duration": duration,
                            }
                        },
                    )
        except Exception as e:
            self.logger.error(f"Failed to mark missing lives as ended: {e}")

    async def get_global_history(
        self, skip: int = 0, limit: int = 20
    ) -> List[Dict[str, Any]]:
        cursor = (
            self.db.global_live_history.find()
            .sort("start_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def get_total_global_history_count(self) -> int:
        return await self.db.global_live_history.count_documents({})
