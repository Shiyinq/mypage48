import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.logging_config import create_logger


class LiveHistoryRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.watched_col = db.watched_live_history
        self.history_col = db.live_history
        self.logger = create_logger("live_history_repository", __name__)

    def _build_date_query(
        self,
        base_query: Dict[str, Any],
        start_date: Optional[datetime.datetime],
        end_date: Optional[datetime.datetime],
        date_field: str = "start_at",
    ) -> Dict[str, Any]:
        query = base_query.copy()
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query[date_field] = date_query
        return query

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

            result = await self.watched_col.update_one(
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
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> List[Dict[str, Any]]:
        query = self._build_date_query(
            {"user_id": user_id}, start_date, end_date, "started_at"
        )
        cursor = (
            self.watched_col.find(query)
            .sort("last_updated_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def get_history_by_user_and_member(
        self,
        user_id: str,
        member_id: str,
        skip: int = 0,
        limit: int = 20,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> List[Dict[str, Any]]:
        query = self._build_date_query(
            {"user_id": user_id, "member_id": member_id},
            start_date,
            end_date,
            "started_at",
        )
        cursor = (
            self.watched_col.find(query)
            .sort("last_updated_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def get_total_history_count(
        self,
        user_id: str,
        member_id: Optional[str] = None,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> int:
        query = {"user_id": user_id}
        if member_id:
            query["member_id"] = member_id
        query = self._build_date_query(query, start_date, end_date, "started_at")
        return await self.watched_col.count_documents(query)

    async def get_overall_stats(
        self,
        user_id: str,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> Dict[str, Any]:
        match_query = self._build_date_query(
            {"user_id": user_id}, start_date, end_date, "started_at"
        )
        pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": "$member_id",
                    "member_name": {"$first": "$member_name"},
                    "total_duration": {"$sum": "$duration"},
                    "watch_count": {"$sum": 1},
                }
            },
            {"$sort": {"watch_count": -1, "total_duration": -1, "member_name": 1}},
        ]
        cursor = self.watched_col.aggregate(pipeline)

        total_duration = 0
        total_watches = 0
        top_member_id = None
        top_member_name = None
        top_member_watches = 0

        member_counts = {}
        member_durations = {}

        is_first = True
        async for doc in cursor:
            member_id = doc["_id"]
            dur = doc["total_duration"]
            watches = doc["watch_count"]
            m_name = doc.get("member_name")

            total_duration += dur
            total_watches += watches

            member_counts[member_id] = watches
            member_durations[member_id] = dur

            if is_first:
                top_member_watches = watches
                top_member_id = member_id
                top_member_name = m_name
                is_first = False

        platform_pipeline = [
            {"$match": match_query},
            {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        ]
        platform_cursor = self.watched_col.aggregate(platform_pipeline)
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
        self,
        user_id: str,
        member_id: str = None,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        query = {"user_id": user_id}
        if member_id:
            query["member_id"] = member_id
        query = self._build_date_query(query, start_date, end_date, "started_at")

        longest_doc = await self.watched_col.find_one(query, sort=[("duration", -1)])

        if not longest_doc:
            return None

        return {
            "duration": longest_doc["duration"],
            "live_title": longest_doc.get("live_title"),
            "platform": longest_doc.get("platform"),
            "started_at": longest_doc.get("started_at"),
            "member_name": longest_doc.get("member_name"),
        }

    async def get_member_stats(
        self,
        user_id: str,
        member_id: str,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> Dict[str, Any]:
        match_query = self._build_date_query(
            {"user_id": user_id, "member_id": member_id},
            start_date,
            end_date,
            "started_at",
        )
        pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": None,
                    "total_duration": {"$sum": "$duration"},
                    "total_watches": {"$sum": 1},
                }
            },
        ]
        cursor = self.watched_col.aggregate(pipeline)
        results = [doc async for doc in cursor]

        if not results:
            return {
                "member_id": member_id,
                "total_duration": 0,
                "total_watches": 0,
                "platform_counts": {},
                "longest_watch": None,
            }

        longest_watch = await self.get_longest_watch(
            user_id, member_id, start_date=start_date, end_date=end_date
        )

        platform_pipeline = [
            {"$match": match_query},
            {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        ]
        platform_cursor = self.watched_col.aggregate(platform_pipeline)
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
            existing = await self.history_col.find_one(
                {"live_id": live_id, "platform": platform}
            )
            now = datetime.datetime.now(datetime.timezone.utc)

            if existing:
                # Update max view_num
                view_num = max(
                    existing.get("view_num", 0), live_data.get("view_num", 0)
                )
                await self.history_col.update_one(
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
                await self.history_col.insert_one(live_data)
        except Exception as e:
            self.logger.error(f"Failed to upsert global live: {e}")

    async def mark_missing_lives_as_ended(self, current_live_ids: List[str]) -> None:
        """Mark lives that are currently 'live' but not in current_live_ids as 'ended'."""
        try:
            # Find all lives currently marked as 'live'
            cursor = self.history_col.find({"status": "live"})
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

                    await self.history_col.update_one(
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
        self,
        skip: int = 0,
        limit: int = 20,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> List[Dict[str, Any]]:
        query = self._build_date_query({}, start_date, end_date)
        cursor = (
            self.history_col.find(query).sort("start_at", -1).skip(skip).limit(limit)
        )
        return [doc async for doc in cursor]

    async def get_total_global_history_count(
        self,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> int:
        query = self._build_date_query({}, start_date, end_date)
        return await self.history_col.count_documents(query)

    async def get_total_watched_live_members_count(
        self,
        user_id: str,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> int:
        match_query = self._build_date_query(
            {"user_id": user_id}, start_date, end_date, "started_at"
        )
        pipeline = [
            {"$match": match_query},
            {"$group": {"_id": "$member_id"}},
            {"$count": "total_members"},
        ]
        cursor = self.watched_col.aggregate(pipeline)
        results = [doc async for doc in cursor]
        return results[0]["total_members"] if results else 0

    async def get_watched_live_members_ranking(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> List[Dict[str, Any]]:
        match_query = self._build_date_query(
            {"user_id": user_id}, start_date, end_date, "started_at"
        )
        pipeline = [
            {"$match": match_query},
            {
                "$group": {
                    "_id": "$member_id",
                    "member_name": {"$first": "$member_name"},
                    "total_duration": {"$sum": "$duration"},
                    "total_watches": {"$sum": 1},
                }
            },
            {"$sort": {"total_watches": -1, "total_duration": -1, "member_name": 1}},
            {
                "$project": {
                    "_id": 0,
                    "member_id": "$_id",
                    "member_name": 1,
                    "total_duration": 1,
                    "total_watches": 1,
                }
            },
            {"$skip": skip},
            {"$limit": limit},
        ]
        cursor = self.watched_col.aggregate(pipeline)
        return [doc async for doc in cursor]

    async def get_global_overall_stats(
        self,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> Dict[str, Any]:
        match_stage = self._build_date_query({}, start_date, end_date)
        match_pipeline = [{"$match": match_stage}] if match_stage else []

        # unique_members_count
        unique_members_pipeline = match_pipeline + [
            {"$group": {"_id": "$member.id"}},
            {"$count": "count"},
        ]
        um_cursor = self.history_col.aggregate(unique_members_pipeline)
        um_results = [doc async for doc in um_cursor]
        unique_members_count = um_results[0]["count"] if um_results else 0

        # platform counts
        platform_pipeline = match_pipeline + [
            {"$group": {"_id": "$platform", "count": {"$sum": 1}}}
        ]
        platform_cursor = self.history_col.aggregate(platform_pipeline)
        platform_counts = {doc["_id"]: doc["count"] async for doc in platform_cursor}

        # total duration and total lives
        totals_pipeline = match_pipeline + [
            {
                "$group": {
                    "_id": None,
                    "total_duration": {"$sum": "$duration"},
                    "total_lives": {"$sum": 1},
                }
            }
        ]
        totals_cursor = self.history_col.aggregate(totals_pipeline)
        totals_results = [doc async for doc in totals_cursor]
        total_duration = totals_results[0]["total_duration"] if totals_results else 0
        total_lives = totals_results[0]["total_lives"] if totals_results else 0

        # top member by frequency
        top_member_pipeline = match_pipeline + [
            {
                "$group": {
                    "_id": "$member.id",
                    "member_name": {"$first": "$member.name"},
                    "total_watches": {"$sum": 1},
                    "total_duration": {"$sum": "$duration"},
                }
            },
            {"$sort": {"total_watches": -1, "total_duration": -1, "member_name": 1}},
            {"$limit": 1},
        ]
        tm_cursor = self.history_col.aggregate(top_member_pipeline)
        tm_results = [doc async for doc in tm_cursor]

        top_member_id = tm_results[0]["_id"] if tm_results else None
        top_member_name = tm_results[0]["member_name"] if tm_results else None
        top_member_watches = tm_results[0]["total_watches"] if tm_results else 0
        top_member_duration = tm_results[0]["total_duration"] if tm_results else 0

        # highest view live
        highest_view_doc = await self.history_col.find_one(
            match_stage, sort=[("view_num", -1)]
        )
        highest_view_live = None
        if highest_view_doc:
            highest_view_live = {
                "duration": highest_view_doc.get(
                    "view_num", 0
                ),  # re-using duration field for view_num count
                "live_title": highest_view_doc.get("title"),
                "platform": highest_view_doc.get("platform"),
                "started_at": highest_view_doc.get("start_at"),
                "member_name": highest_view_doc.get("member", {}).get("name"),
            }

        return {
            "total_lives": total_lives,
            "total_duration": total_duration,
            "unique_members_count": unique_members_count,
            "top_member_id": top_member_id,
            "top_member_name": top_member_name,
            "top_member_watches": top_member_watches,
            "top_member_duration": top_member_duration,
            "platform_counts": platform_counts,
            "highest_view_live": highest_view_live,
        }

    async def get_global_live_members_ranking(
        self,
        skip: int = 0,
        limit: int = 20,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> List[Dict[str, Any]]:
        match_stage = self._build_date_query({}, start_date, end_date)
        match_pipeline = [{"$match": match_stage}] if match_stage else []

        pipeline = match_pipeline + [
            {
                "$group": {
                    "_id": "$member.id",
                    "member_name": {"$first": "$member.name"},
                    "total_duration": {"$sum": "$duration"},
                    "total_watches": {"$sum": 1},
                }
            },
            {"$sort": {"total_watches": -1, "total_duration": -1, "member_name": 1}},
            {
                "$project": {
                    "_id": 0,
                    "member_id": "$_id",
                    "member_name": 1,
                    "total_duration": 1,
                    "total_watches": 1,
                }
            },
            {"$skip": skip},
            {"$limit": limit},
        ]
        cursor = self.history_col.aggregate(pipeline)
        return [doc async for doc in cursor]

    async def get_total_global_live_members_count(
        self,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> int:
        match_stage = self._build_date_query({}, start_date, end_date)
        match_pipeline = [{"$match": match_stage}] if match_stage else []

        pipeline = match_pipeline + [
            {"$group": {"_id": "$member.id"}},
            {"$count": "total_members"},
        ]
        cursor = self.history_col.aggregate(pipeline)
        results = [doc async for doc in cursor]
        return results[0]["total_members"] if results else 0

    async def get_global_history_by_member(
        self,
        member_id: str,
        skip: int = 0,
        limit: int = 20,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> List[Dict[str, Any]]:
        query = self._build_date_query({"member.id": member_id}, start_date, end_date)
        cursor = (
            self.history_col.find(query).sort("start_at", -1).skip(skip).limit(limit)
        )
        return [doc async for doc in cursor]

    async def get_total_global_history_count_by_member(
        self,
        member_id: str,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> int:
        query = self._build_date_query({"member.id": member_id}, start_date, end_date)
        return await self.history_col.count_documents(query)

    async def get_global_member_stats(
        self,
        member_id: str,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> Dict[str, Any]:
        match_stage = self._build_date_query(
            {"member.id": member_id}, start_date, end_date
        )
        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": "$platform",
                    "total_duration": {"$sum": "$duration"},
                    "watches": {"$sum": 1},
                }
            },
        ]

        cursor = self.history_col.aggregate(pipeline)

        total_duration = 0
        total_watches = 0
        platform_counts = {}

        async for doc in cursor:
            platform = doc["_id"]
            duration = doc["total_duration"]
            watches = doc["watches"]

            total_duration += duration
            total_watches += watches
            platform_counts[platform] = watches

        # Get longest watch
        longest_watch_query = self._build_date_query(
            {"member.id": member_id}, start_date, end_date
        )
        longest_watch_doc = await self.history_col.find_one(
            longest_watch_query, sort=[("duration", -1)]
        )

        longest_watch = None
        if longest_watch_doc:
            longest_watch = {
                "duration": longest_watch_doc.get("duration", 0),
                "live_title": longest_watch_doc.get("title"),
                "platform": longest_watch_doc.get("platform"),
                "started_at": longest_watch_doc.get("start_at"),
                "member_name": longest_watch_doc.get("member", {}).get("name"),
            }

        return {
            "member_id": member_id,
            "total_duration": total_duration,
            "total_lives": total_watches,
            "platform_counts": platform_counts,
            "longest_live": longest_watch,
        }

    async def get_pc_collection(
        self,
        user_id: Optional[str],
        collection_type: str = "all",
        skip: int = 0,
        limit: int = 20,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
        sort_by: str = "date_desc",
    ) -> List[Dict[str, Any]]:
        query = self._build_date_query({}, start_date, end_date)

        watched_live_ids = []
        if user_id and collection_type in ["owned", "unowned", "all"]:
            watched_live_ids = await self.watched_col.distinct(
                "live_id", {"user_id": user_id}
            )

        if user_id and collection_type == "owned":
            query["live_id"] = {"$in": watched_live_ids}
        elif user_id and collection_type == "unowned":
            query["live_id"] = {"$nin": watched_live_ids}

        sort_stage = [("start_at", -1)]
        if sort_by == "date_asc":
            sort_stage = [("start_at", 1)]
        elif sort_by == "tier_desc":
            sort_stage = [("view_num", -1), ("start_at", -1)]
        elif sort_by == "tier_asc":
            sort_stage = [("view_num", 1), ("start_at", 1)]

        cursor = self.history_col.find(query).sort(sort_stage).skip(skip).limit(limit)
        results = [doc async for doc in cursor]

        if user_id and collection_type == "owned":
            for r in results:
                r["is_owned"] = True
        elif user_id and collection_type == "unowned":
            for r in results:
                r["is_owned"] = False
        else:
            watched_set = set(watched_live_ids)
            for r in results:
                r["is_owned"] = r.get("live_id") in watched_set if user_id else False

        return results

    async def get_total_pc_collection_count(
        self,
        user_id: Optional[str],
        collection_type: str = "all",
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
    ) -> int:
        query = self._build_date_query({}, start_date, end_date)

        if user_id and collection_type in ["owned", "unowned"]:
            watched_live_ids = await self.watched_col.distinct(
                "live_id", {"user_id": user_id}
            )
            if collection_type == "owned":
                query["live_id"] = {"$in": watched_live_ids}
            else:
                query["live_id"] = {"$nin": watched_live_ids}

        return await self.history_col.count_documents(query)
