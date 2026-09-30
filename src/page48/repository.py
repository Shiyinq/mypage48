from datetime import datetime
from typing import Dict, List, Optional

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class Page48Repository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.posts = db["page48_posts"]
        self.likes = db["page48_likes"]
        self.bookmarks = db["page48_bookmarks"]
        self.reposts = db["page48_reposts"]
        self.reports = db["page48_reports"]

    async def insert_post(self, post_data: dict):
        return await self.posts.insert_one(post_data)

    async def get_post_by_id(self, post_id: str) -> Optional[dict]:
        return await self.posts.find_one({"postId": post_id})

    async def get_posts_by_ids(self, post_ids: List[str]) -> List[dict]:
        if not post_ids:
            return []
        return await self.posts.find({"postId": {"$in": post_ids}}).to_list(length=None)

    async def update_post(self, post_id: str, update_data: dict):
        return await self.posts.update_one({"postId": post_id}, {"$set": update_data})

    async def delete_post(self, post_id: str):
        return await self.posts.delete_one({"postId": post_id})

    async def increment_post_stats(self, post_id: str, field: str, amount: int = 1):
        return await self.posts.update_one(
            {"postId": post_id}, {"$inc": {field: amount}}
        )

    @staticmethod
    def _media_query(media: Optional[str]) -> dict:
        """Build a Mongo filter for a feed media type."""
        if media == "image":
            return {"images": {"$exists": True, "$ne": []}}
        if media == "video":
            return {"videos": {"$exists": True, "$ne": []}}
        if media == "text":
            return {
                "$and": [
                    {"$or": [{"images": {"$exists": False}}, {"images": {"$size": 0}}]},
                    {"$or": [{"videos": {"$exists": False}}, {"videos": {"$size": 0}}]},
                ]
            }
        return {}

    async def get_feed(
        self,
        limit: int = 20,
        cursor: Optional[dict] = None,
        media: Optional[str] = None,
    ) -> List[dict]:
        conditions: List[dict] = [{"parentPostId": None}]

        media_filter = self._media_query(media)
        if media_filter:
            conditions.append(media_filter)

        if cursor:
            conditions.append(
                {
                    "$or": [
                        {"createdAt": {"$lt": cursor["createdAt"]}},
                        {
                            "createdAt": cursor["createdAt"],
                            "postId": {"$lt": cursor["postId"]},
                        },
                    ]
                }
            )

        query = {"$and": conditions}
        cursor_obj = (
            self.posts.find(query)
            .sort([("createdAt", -1), ("postId", -1)])
            .limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

    async def get_thread_replies(self, root_post_id: str) -> List[dict]:
        # returns all replies for a thread
        cursor_obj = self.posts.find({"rootPostId": root_post_id}).sort("createdAt", 1)
        return await cursor_obj.to_list(length=None)

    async def get_direct_replies(
        self, parent_post_id: str, limit: int = 20, cursor: Optional[dict] = None
    ) -> List[dict]:
        query = {"parentPostId": parent_post_id}
        if cursor:
            query["$or"] = [
                {"createdAt": {"$lt": cursor["createdAt"]}},
                {"createdAt": cursor["createdAt"], "postId": {"$lt": cursor["postId"]}},
            ]

        cursor_obj = (
            self.posts.find(query)
            .sort([("createdAt", -1), ("postId", -1)])
            .limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

    async def get_user_posts(
        self,
        username: str,
        limit: int = 20,
        cursor: Optional[dict] = None,
        media: Optional[str] = None,
    ) -> List[dict]:
        conditions: List[dict] = [{"username": username, "parentPostId": None}]

        media_filter = self._media_query(media)
        if media_filter:
            conditions.append(media_filter)

        if cursor:
            conditions.append(
                {
                    "$or": [
                        {"createdAt": {"$lt": cursor["createdAt"]}},
                        {
                            "createdAt": cursor["createdAt"],
                            "postId": {"$lt": cursor["postId"]},
                        },
                    ]
                }
            )

        query = {"$and": conditions}
        cursor_obj = (
            self.posts.find(query)
            .sort([("createdAt", -1), ("postId", -1)])
            .limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

    async def get_user_replies(
        self, username: str, limit: int = 20, cursor: Optional[dict] = None
    ) -> List[dict]:
        query = {"username": username, "parentPostId": {"$ne": None}}
        if cursor:
            query["$or"] = [
                {"createdAt": {"$lt": cursor["createdAt"]}},
                {"createdAt": cursor["createdAt"], "postId": {"$lt": cursor["postId"]}},
            ]

        cursor_obj = (
            self.posts.find(query)
            .sort([("createdAt", -1), ("postId", -1)])
            .limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

    async def count_user_posts(self, username: str) -> int:
        return await self.posts.count_documents(
            {"username": username, "parentPostId": None}
        )

    async def get_most_active_users(
        self, limit: int = 5, since: Optional[datetime] = None
    ) -> List[dict]:
        """Top-level posters in a time window, most posts first."""
        match: dict = {"parentPostId": None}
        if since is not None:
            match["createdAt"] = {"$gte": since}

        pipeline = [
            {"$match": match},
            {"$sort": {"createdAt": -1}},
            {
                "$group": {
                    "_id": "$userId",
                    "postCount": {"$sum": 1},
                    "username": {"$last": "$username"},
                    "name": {"$last": "$userDisplayName"},
                    "lastPostedAt": {"$max": "$createdAt"},
                }
            },
            {"$sort": {"postCount": -1, "lastPostedAt": -1}},
            {"$limit": limit},
        ]
        cursor = self.posts.aggregate(pipeline)
        return await cursor.to_list(length=limit)

    async def get_trending_tags(self, limit: int = 10) -> List[dict]:
        """Return the most used tags across all posts, most frequent first."""
        pipeline = [
            {"$match": {"tags": {"$exists": True, "$ne": []}}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
            {"$limit": limit},
        ]
        cursor = self.posts.aggregate(pipeline)
        return await cursor.to_list(length=limit)

    async def get_posts_by_tag(
        self,
        tag: str,
        limit: int = 20,
        cursor: Optional[dict] = None,
        media: Optional[str] = None,
    ) -> List[dict]:
        conditions: List[dict] = [{"tags": tag}]

        media_filter = self._media_query(media)
        if media_filter:
            conditions.append(media_filter)

        if cursor:
            conditions.append(
                {
                    "$or": [
                        {"createdAt": {"$lt": cursor["createdAt"]}},
                        {
                            "createdAt": cursor["createdAt"],
                            "postId": {"$lt": cursor["postId"]},
                        },
                    ]
                }
            )

        query = {"$and": conditions}
        cursor_obj = (
            self.posts.find(query)
            .sort([("createdAt", -1), ("postId", -1)])
            .limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

    # Likes
    async def get_like(self, post_id: str, user_id: str) -> Optional[dict]:
        return await self.likes.find_one({"postId": post_id, "userId": user_id})

    async def insert_like(self, post_id: str, user_id: str):
        return await self.likes.insert_one(
            {"postId": post_id, "userId": user_id, "createdAt": datetime.now()}
        )

    async def delete_like(self, post_id: str, user_id: str):
        return await self.likes.delete_one({"postId": post_id, "userId": user_id})

    async def get_user_likes(
        self, user_id: str, limit: int = 20, cursor: Optional[dict] = None
    ) -> dict:
        query = {"userId": user_id}
        if cursor:
            cursor_id = cursor["_id"]
            if isinstance(cursor_id, str):
                try:
                    cursor_id = ObjectId(cursor_id)
                except Exception:
                    pass
            query["$or"] = [
                {"createdAt": {"$lt": cursor["createdAt"]}},
                {"createdAt": cursor["createdAt"], "_id": {"$lt": cursor_id}},
            ]

        cursor_obj = (
            self.likes.find(query).sort([("createdAt", -1), ("_id", -1)]).limit(limit)
        )
        like_list = await cursor_obj.to_list(length=limit)

        if not like_list:
            return {"likes": [], "posts": []}

        post_ids = [like["postId"] for like in like_list]
        posts = await self.posts.find({"postId": {"$in": post_ids}}).to_list(
            length=None
        )

        return {"likes": like_list, "posts": posts}

    # Bookmarks
    async def get_bookmark(self, post_id: str, user_id: str) -> Optional[dict]:
        return await self.bookmarks.find_one({"postId": post_id, "userId": user_id})

    async def insert_bookmark(self, post_id: str, user_id: str):
        return await self.bookmarks.insert_one(
            {"postId": post_id, "userId": user_id, "createdAt": datetime.now()}
        )

    async def delete_bookmark(self, post_id: str, user_id: str):
        return await self.bookmarks.delete_one({"postId": post_id, "userId": user_id})

    async def get_user_bookmarks(
        self, user_id: str, limit: int = 20, cursor: Optional[dict] = None
    ) -> dict:
        query = {"userId": user_id}
        if cursor:
            cursor_id = cursor["_id"]
            if isinstance(cursor_id, str):
                try:
                    cursor_id = ObjectId(cursor_id)
                except Exception:
                    pass
            query["$or"] = [
                {"createdAt": {"$lt": cursor["createdAt"]}},
                {"createdAt": cursor["createdAt"], "_id": {"$lt": cursor_id}},
            ]

        cursor_obj = (
            self.bookmarks.find(query)
            .sort([("createdAt", -1), ("_id", -1)])
            .limit(limit)
        )
        bookmark_list = await cursor_obj.to_list(length=limit)

        if not bookmark_list:
            return {"bookmarks": [], "posts": []}

        post_ids = [b["postId"] for b in bookmark_list]

        posts = await self.posts.find({"postId": {"$in": post_ids}}).to_list(
            length=None
        )

        return {"bookmarks": bookmark_list, "posts": posts}

    # Reposts
    async def get_repost(self, post_id: str, user_id: str) -> Optional[dict]:
        return await self.reposts.find_one({"postId": post_id, "userId": user_id})

    async def insert_repost(self, post_id: str, user_id: str):
        return await self.reposts.insert_one(
            {"postId": post_id, "userId": user_id, "createdAt": datetime.now()}
        )

    async def delete_repost(self, post_id: str, user_id: str):
        return await self.reposts.delete_one({"postId": post_id, "userId": user_id})

    async def count_user_reposts(self, user_id: str) -> int:
        return await self.reposts.count_documents({"userId": user_id})

    async def get_user_reposts(
        self, user_id: str, limit: int = 20, cursor: Optional[dict] = None
    ) -> dict:
        query = {"userId": user_id}
        if cursor:
            cursor_id = cursor["_id"]
            if isinstance(cursor_id, str):
                try:
                    cursor_id = ObjectId(cursor_id)
                except Exception:
                    pass
            query["$or"] = [
                {"createdAt": {"$lt": cursor["createdAt"]}},
                {"createdAt": cursor["createdAt"], "_id": {"$lt": cursor_id}},
            ]

        cursor_obj = (
            self.reposts.find(query).sort([("createdAt", -1), ("_id", -1)]).limit(limit)
        )
        repost_list = await cursor_obj.to_list(length=limit)

        if not repost_list:
            return {"reposts": [], "posts": []}

        post_ids = [r["postId"] for r in repost_list]
        posts = await self.posts.find({"postId": {"$in": post_ids}}).to_list(
            length=None
        )

        return {"reposts": repost_list, "posts": posts}

    # Reports
    async def insert_report(self, report_data: dict):
        return await self.reports.insert_one(report_data)

    async def get_report(
        self, reporter_user_id: str, target_type: str, target_id: str
    ) -> Optional[dict]:
        return await self.reports.find_one(
            {
                "reporterUserId": reporter_user_id,
                "targetType": target_type,
                "targetId": target_id,
            }
        )

    @staticmethod
    def _reports_query(
        target_type: Optional[str] = None, status: Optional[str] = None
    ) -> dict:
        conditions: List[dict] = []
        if target_type:
            conditions.append({"targetType": target_type})
        if status:
            conditions.append({"status": status})
        if not conditions:
            return {}
        return {"$and": conditions}

    async def get_reports(
        self,
        limit: int = 20,
        cursor: Optional[dict] = None,
        target_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[dict]:
        conditions: List[dict] = []
        base = self._reports_query(target_type, status)
        if base:
            conditions.append(base)
        if cursor:
            conditions.append(
                {
                    "$or": [
                        {"createdAt": {"$lt": cursor["createdAt"]}},
                        {
                            "createdAt": cursor["createdAt"],
                            "reportId": {"$lt": cursor["reportId"]},
                        },
                    ]
                }
            )

        query = {"$and": conditions} if conditions else {}
        cursor_obj = (
            self.reports.find(query)
            .sort([("createdAt", -1), ("reportId", -1)])
            .limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

    async def count_reports(
        self, target_type: Optional[str] = None, status: Optional[str] = None
    ) -> int:
        return await self.reports.count_documents(
            self._reports_query(target_type, status)
        )

    async def get_user_interactions(
        self, post_ids: List[str], user_id: str
    ) -> Dict[str, Dict[str, bool]]:
        """Batch get user interactions for a list of posts."""
        if not post_ids or not user_id:
            return {
                pid: {"isLiked": False, "isBookmarked": False, "isReposted": False}
                for pid in post_ids
            }

        likes = await self.likes.find(
            {"userId": user_id, "postId": {"$in": post_ids}}
        ).to_list(length=None)
        bookmarks = await self.bookmarks.find(
            {"userId": user_id, "postId": {"$in": post_ids}}
        ).to_list(length=None)
        reposts = await self.reposts.find(
            {"userId": user_id, "postId": {"$in": post_ids}}
        ).to_list(length=None)

        liked_set = {l["postId"] for l in likes}
        bookmarked_set = {b["postId"] for b in bookmarks}
        reposted_set = {r["postId"] for r in reposts}

        result = {}
        for pid in post_ids:
            result[pid] = {
                "isLiked": pid in liked_set,
                "isBookmarked": pid in bookmarked_set,
                "isReposted": pid in reposted_set,
            }
        return result
