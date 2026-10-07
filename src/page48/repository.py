from datetime import datetime, timezone
import re
from typing import Dict, List, Optional

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

# A search query may sort its matches on disk, but it must never hang a request.
SEARCH_MAX_TIME_MS = 5000
# Posts scanned when counting tag matches; bounds the aggregation's work.
SEARCH_TAG_POST_SCAN = 20000
# Posts a trending-tags / most-active aggregation will scan. Both run for
# unauthenticated callers, so an unbounded `$unwind`/`$group` over the whole
# collection would be a cheap way to exhaust the database.
AGGREGATION_POST_SCAN = 20000
# How many block/mute edges one lookup will read before giving up on the rest.
RELATION_SCAN_LIMIT = 5000
# A follow is accepted unless it is explicitly waiting for the target's approval.
# Legacy rows predate the field entirely, so "not pending" is the safe test.
ACCEPTED_FOLLOW = {"status": {"$ne": "pending"}}


class Page48Repository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.posts = db["page48_posts"]
        self.likes = db["page48_likes"]
        self.bookmarks = db["page48_bookmarks"]
        self.reposts = db["page48_reposts"]
        self.reports = db["page48_reports"]
        self.poll_votes = db["page48_poll_votes"]
        self.follows = db["page48_follows"]
        self.notifications = db["page48_notifications"]
        self.blocks = db["page48_blocks"]
        self.mutes = db["page48_mutes"]

    async def insert_post(self, post_data: dict):
        return await self.posts.insert_one(post_data)

    async def get_post_by_id(self, post_id: str) -> Optional[dict]:
        return await self.posts.find_one({"postId": post_id})

    async def get_posts_by_ids(
        self, post_ids: List[str], visibility: Optional[dict] = None
    ) -> List[dict]:
        if not post_ids:
            return []
        query: dict = {"postId": {"$in": post_ids}}
        if visibility:
            query = {"$and": [query, visibility]}
        return await self.posts.find(query).to_list(length=None)

    async def get_posts_by_root_ids(self, root_ids: List[str]) -> List[dict]:
        """Every post that belongs to the given threads (roots excluded)."""
        if not root_ids:
            return []

        return await self.posts.find(
            {"rootPostId": {"$in": root_ids}, "parentPostId": {"$ne": None}}
        ).to_list(length=None)

    async def update_post(self, post_id: str, update_data: dict):
        return await self.posts.update_one({"postId": post_id}, {"$set": update_data})

    async def delete_post(self, post_id: str):
        return await self.posts.delete_one({"postId": post_id})

    async def increment_post_stats(self, post_id: str, field: str, amount: int = 1):
        return await self.posts.update_one(
            {"postId": post_id}, {"$inc": {field: amount}}
        )

    async def get_pinned_post(
        self, user_id: str, visibility: Optional[dict] = None
    ) -> Optional[dict]:
        query: dict = {"userId": user_id, "pinnedAt": {"$ne": None}}
        if visibility:
            query = {"$and": [query, visibility]}
        return await self.posts.find_one(query)

    async def pin_post(self, post_id: str, user_id: str, pinned_at: datetime):
        """Pin one post per user; any previous pin by the same user is cleared."""
        await self.posts.update_many(
            {"userId": user_id, "pinnedAt": {"$ne": None}},
            {"$set": {"pinnedAt": None}},
        )
        return await self.posts.update_one(
            {"postId": post_id}, {"$set": {"pinnedAt": pinned_at}}
        )

    async def unpin_post(self, post_id: str):
        return await self.posts.update_one(
            {"postId": post_id}, {"$set": {"pinnedAt": None}}
        )

    async def set_post_private(self, post_id: str, user_id: str, is_private: bool):
        """A private post is readable only by its author. A thread is toggled as
        one unit, so the author's own continuations follow the first segment."""
        return await self.posts.update_many(
            {
                "$or": [
                    {"postId": post_id},
                    {"rootPostId": post_id, "userId": user_id},
                ]
            },
            {"$set": {"isPrivate": is_private}},
        )

    async def get_self_continuation(
        self, post_id: str, user_id: str
    ) -> Optional[dict]:
        """The author's own next post in a thread, if this one has one."""
        return await self.posts.find_one(
            {"parentPostId": post_id, "userId": user_id},
            sort=[("createdAt", 1)],
        )

    async def relink_continuation(
        self, continuation_id: str, parent_post_id: Optional[str], depth: int = 0
    ):
        """Reattach a continuation after the post it answered was deleted."""
        update = {"parentPostId": parent_post_id, "depth": depth}
        if parent_post_id is None:
            # The deleted post was the thread root, so the continuation takes over.
            update["rootPostId"] = None
        return await self.posts.update_one({"postId": continuation_id}, {"$set": update})

    async def repoint_thread_root(
        self, old_root_id: str, new_root_id: str, user_id: str
    ):
        """Move the author's descendants of a deleted root under the continuation
        that replaced it, so the thread stays reachable from one root."""
        return await self.posts.update_many(
            {"rootPostId": old_root_id, "userId": user_id},
            {"$set": {"rootPostId": new_root_id}},
        )

    @staticmethod
    def _media_query(media: Optional[str]) -> dict:
        """Build a Mongo filter for a feed media type."""
        if media == "image":
            return {"images": {"$exists": True, "$ne": []}}
        if media == "video":
            return {"videos": {"$exists": True, "$ne": []}}
        if media == "media":
            # Search's media tab: a photo or a video both count as media.
            return {
                "$or": [
                    {"images": {"$exists": True, "$ne": []}},
                    {"videos": {"$exists": True, "$ne": []}},
                ]
            }
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
        author_ids: Optional[List[str]] = None,
        visibility: Optional[dict] = None,
        muted_author_ids: Optional[List[str]] = None,
    ) -> List[dict]:
        conditions: List[dict] = [{"parentPostId": None}]

        # Authors this viewer must not read posts from (blocked, or a locked
        # account they do not follow). The service passes it so every list that
        # returns posts applies the same rule.
        if visibility:
            conditions.append(visibility)

        # Muting only hides someone from the timeline: their posts stay findable
        # in search and readable on their profile.
        if muted_author_ids:
            conditions.append({"userId": {"$nin": muted_author_ids}})

        # Used by the "following" feed: only posts written by the given authors.
        if author_ids is not None:
            conditions.append({"userId": {"$in": author_ids}})

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

    async def get_thread_replies(
        self, root_post_id: str, visibility: Optional[dict] = None
    ) -> List[dict]:
        # returns all replies for a thread
        query: dict = {"rootPostId": root_post_id}
        if visibility:
            query = {"$and": [query, visibility]}
        cursor_obj = self.posts.find(query).sort("createdAt", 1)
        return await cursor_obj.to_list(length=None)

    async def get_direct_replies(
        self,
        parent_post_id: str,
        limit: int = 20,
        cursor: Optional[dict] = None,
        visibility: Optional[dict] = None,
    ) -> List[dict]:
        query = {"parentPostId": parent_post_id}
        if cursor:
            query["$or"] = [
                {"createdAt": {"$lt": cursor["createdAt"]}},
                {"createdAt": cursor["createdAt"], "postId": {"$lt": cursor["postId"]}},
            ]
        if visibility:
            query = {"$and": [query, visibility]}

        cursor_obj = (
            self.posts.find(query)
            .sort([("createdAt", -1), ("postId", -1)])
            .limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

    async def get_user_posts(
        self,
        user_id: str,
        limit: int = 20,
        cursor: Optional[dict] = None,
        media: Optional[str] = None,
        visibility: Optional[dict] = None,
    ) -> List[dict]:
        # Posts are keyed by the immutable `userId`, never by `username`: a user
        # may rename themselves and their posts must stay attached to them.
        conditions: List[dict] = [{"userId": user_id}]

        if visibility:
            conditions.append(visibility)

        # The Photos/Videos tabs collect every image or video the user attached,
        # replies included; the plain post list stays top-level posts only.
        if media not in ("image", "video"):
            conditions.append({"parentPostId": None})

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
        self,
        user_id: str,
        limit: int = 20,
        cursor: Optional[dict] = None,
        visibility: Optional[dict] = None,
    ) -> List[dict]:
        query = {"userId": user_id, "parentPostId": {"$ne": None}}
        if cursor:
            query["$or"] = [
                {"createdAt": {"$lt": cursor["createdAt"]}},
                {"createdAt": cursor["createdAt"], "postId": {"$lt": cursor["postId"]}},
            ]
        if visibility:
            query = {"$and": [query, visibility]}

        cursor_obj = (
            self.posts.find(query)
            .sort([("createdAt", -1), ("postId", -1)])
            .limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

    async def count_user_posts(self, user_id: str) -> int:
        return await self.posts.count_documents(
            {"userId": user_id, "parentPostId": None}
        )

    async def get_most_active_users(
        self,
        limit: int = 5,
        since: Optional[datetime] = None,
        visibility: Optional[dict] = None,
    ) -> List[dict]:
        """Top-level posters in a time window, most posts first."""
        match: dict = {"parentPostId": None}
        if since is not None:
            match["createdAt"] = {"$gte": since}
        if visibility:
            match.update(visibility)

        pipeline = [
            {"$match": match},
            {"$sort": {"createdAt": -1}},
            # Bound the work: only the window's newest posts are grouped. Past
            # this ceiling the ranking is a sample, which is fine for a widget.
            {"$limit": AGGREGATION_POST_SCAN},
            {
                "$group": {
                    "_id": "$userId",
                    "postCount": {"$sum": 1},
                    "lastPostedAt": {"$max": "$createdAt"},
                }
            },
            {"$sort": {"postCount": -1, "lastPostedAt": -1}},
            {"$limit": limit},
        ]
        cursor = self.posts.aggregate(pipeline)
        return await cursor.to_list(length=limit)

    # Search
    async def search_posts(
        self,
        filters: dict,
        limit: int = 20,
        cursor: Optional[dict] = None,
        visibility: Optional[dict] = None,
    ) -> List[dict]:
        """Posts matching a parsed search query, newest first.

        Free words match token *prefixes* (`oline` finds `olinecintaku`), which is
        the one shape MongoDB can answer from an index instead of scanning every
        post in the collection.
        """
        conditions: List[dict] = []

        for word in filters.get("words") or []:
            conditions.append({"searchTokens": {"$regex": f"^{re.escape(word)}"}})
        for tag in filters.get("tags") or []:
            conditions.append({"tags": {"$regex": f"^{re.escape(tag)}"}})
        for mention in filters.get("mentions") or []:
            conditions.append({"mentions": {"$regex": f"^{re.escape(mention)}"}})

        author_ids = filters.get("author_ids")
        # An empty list means "no `from:` filter"; an empty `$in` would match nothing.
        if author_ids:
            conditions.append({"userId": {"$in": author_ids}})

        media_filter = self._media_query(filters.get("media"))
        if media_filter:
            conditions.append(media_filter)

        if not conditions:
            # Nothing to match on. `$and: []` is an error, and an unfiltered list
            # would be worse, so an empty filter simply matches nothing. Checked
            # before visibility so the viewer's own filter cannot mask this.
            return []

        if visibility:
            conditions.append(visibility)

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

        # The token match is served by an index, but the recency sort cannot be: a
        # multikey index holds one entry per token, so it can never provide a sort
        # key. The sort therefore happens in memory, and `allowDiskUse` lets it
        # spill to disk instead of failing on a popular word. That keeps every post
        # searchable — old ones included — and `maxTimeMS` bounds the worst case
        # rather than letting one query hang.
        pipeline: List[dict] = [
            {"$match": {"$and": conditions}},
            {"$sort": {"createdAt": -1, "postId": -1}},
            {"$limit": limit},
        ]
        cursor_obj = self.posts.aggregate(
            pipeline, allowDiskUse=True, maxTimeMS=SEARCH_MAX_TIME_MS
        )
        return await cursor_obj.to_list(length=limit)

    async def search_tags(
        self, term: str, limit: int = 30, visibility: Optional[dict] = None
    ) -> List[dict]:
        """Tags starting with `term`, most used first."""
        if not term:
            return []
        prefix = {"$regex": f"^{re.escape(term)}"}
        match: dict = {"tags": prefix}
        if visibility:
            match.update(visibility)
        pipeline = [
            {"$match": match},
            # Bounded work: the counts stay exact at a realistic scale and only
            # become a sample past this ceiling. `$limit` before `$unwind` keeps
            # the unwound set small, and the whole scan stops there.
            {"$limit": SEARCH_TAG_POST_SCAN},
            {"$unwind": "$tags"},
            {"$match": {"tags": prefix}},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1, "_id": 1}},
            {"$limit": limit},
        ]
        cursor = self.posts.aggregate(pipeline)
        return await cursor.to_list(length=limit)

    async def get_trending_tags(
        self, limit: int = 10, visibility: Optional[dict] = None
    ) -> List[dict]:
        """Return the most used tags across all posts, most frequent first."""
        match: dict = {"tags": {"$exists": True, "$ne": []}}
        if visibility:
            match.update(visibility)
        pipeline = [
            {"$match": match},
            # Bound the work before unwinding; counts stay exact at a realistic
            # scale and become a sample past the ceiling (like `search_tags`).
            {"$limit": AGGREGATION_POST_SCAN},
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
        visibility: Optional[dict] = None,
    ) -> List[dict]:
        conditions: List[dict] = [{"tags": tag}]

        if visibility:
            conditions.append(visibility)

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
            {
                "postId": post_id,
                "userId": user_id,
                "createdAt": datetime.now(timezone.utc),
            }
        )

    async def delete_like(self, post_id: str, user_id: str):
        return await self.likes.delete_one({"postId": post_id, "userId": user_id})

    async def get_user_likes(
        self,
        user_id: str,
        limit: int = 20,
        cursor: Optional[dict] = None,
        visibility: Optional[dict] = None,
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
        post_query: dict = {"postId": {"$in": post_ids}}
        if visibility:
            post_query = {"$and": [post_query, visibility]}
        posts = await self.posts.find(post_query).to_list(length=None)

        return {"likes": like_list, "posts": posts}

    # Bookmarks
    async def get_bookmark(self, post_id: str, user_id: str) -> Optional[dict]:
        return await self.bookmarks.find_one({"postId": post_id, "userId": user_id})

    async def insert_bookmark(self, post_id: str, user_id: str):
        return await self.bookmarks.insert_one(
            {
                "postId": post_id,
                "userId": user_id,
                "createdAt": datetime.now(timezone.utc),
            }
        )

    async def delete_bookmark(self, post_id: str, user_id: str):
        return await self.bookmarks.delete_one({"postId": post_id, "userId": user_id})

    async def get_user_bookmarks(
        self,
        user_id: str,
        limit: int = 20,
        cursor: Optional[dict] = None,
        visibility: Optional[dict] = None,
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

        post_query: dict = {"postId": {"$in": post_ids}}
        if visibility:
            post_query = {"$and": [post_query, visibility]}
        posts = await self.posts.find(post_query).to_list(length=None)

        return {"bookmarks": bookmark_list, "posts": posts}

    # Reposts
    async def get_repost(self, post_id: str, user_id: str) -> Optional[dict]:
        return await self.reposts.find_one({"postId": post_id, "userId": user_id})

    async def insert_repost(self, post_id: str, user_id: str):
        return await self.reposts.insert_one(
            {
                "postId": post_id,
                "userId": user_id,
                "createdAt": datetime.now(timezone.utc),
            }
        )

    async def delete_repost(self, post_id: str, user_id: str):
        return await self.reposts.delete_one({"postId": post_id, "userId": user_id})

    async def count_user_reposts(self, user_id: str) -> int:
        return await self.reposts.count_documents({"userId": user_id})

    async def get_user_reposts(
        self,
        user_id: str,
        limit: int = 20,
        cursor: Optional[dict] = None,
        visibility: Optional[dict] = None,
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
        post_query: dict = {"postId": {"$in": post_ids}}
        if visibility:
            post_query = {"$and": [post_query, visibility]}
        posts = await self.posts.find(post_query).to_list(length=None)

        return {"reposts": repost_list, "posts": posts}

    # Per-post interactions (the "activity" lists)
    @staticmethod
    def _with_interaction_cursor(query: dict, cursor: Optional[dict]) -> dict:
        """Narrow a query to rows older than `cursor` (createdAt + ObjectId)."""
        if not cursor:
            return query
        cursor_id = cursor.get("_id")
        if isinstance(cursor_id, str):
            try:
                cursor_id = ObjectId(cursor_id)
            except Exception:
                pass
        query["$or"] = [
            {"createdAt": {"$lt": cursor["createdAt"]}},
            {"createdAt": cursor["createdAt"], "_id": {"$lt": cursor_id}},
        ]
        return query

    async def count_post_quotes(
        self, post_id: str, visibility: Optional[dict] = None
    ) -> int:
        query: dict = {"quotedPostId": post_id}
        if visibility:
            query = {"$and": [query, visibility]}
        return await self.posts.count_documents(query)

    async def count_quotes_for_posts(self, post_ids: List[str]) -> Dict[str, int]:
        """Quote counts for many posts in one query, keyed by the quoted postId."""
        if not post_ids:
            return {}

        pipeline = [
            {"$match": {"quotedPostId": {"$in": post_ids}}},
            {"$group": {"_id": "$quotedPostId", "count": {"$sum": 1}}},
        ]
        cursor = self.posts.aggregate(pipeline)
        rows = await cursor.to_list(length=None)
        return {row["_id"]: row["count"] for row in rows}

    async def count_post_reposts(
        self, post_id: str, visibility: Optional[dict] = None
    ) -> int:
        query: dict = {"postId": post_id}
        if visibility:
            query = {"$and": [query, visibility]}
        return await self.reposts.count_documents(query)

    async def count_post_likes(
        self, post_id: str, visibility: Optional[dict] = None
    ) -> int:
        query: dict = {"postId": post_id}
        if visibility:
            query = {"$and": [query, visibility]}
        return await self.likes.count_documents(query)

    async def get_post_quotes(
        self,
        post_id: str,
        limit: int = 20,
        cursor: Optional[dict] = None,
        visibility: Optional[dict] = None,
    ) -> List[dict]:
        """Posts that quote the given post, newest first."""
        query: dict = {"quotedPostId": post_id}
        if cursor:
            query["$or"] = [
                {"createdAt": {"$lt": cursor["createdAt"]}},
                {"createdAt": cursor["createdAt"], "postId": {"$lt": cursor["postId"]}},
            ]
        if visibility:
            query = {"$and": [query, visibility]}

        cursor_obj = (
            self.posts.find(query)
            .sort([("createdAt", -1), ("postId", -1)])
            .limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

    async def get_post_reposts(
        self, post_id: str, limit: int = 20, cursor: Optional[dict] = None
    ) -> List[dict]:
        """Repost rows for a post, newest first."""
        query = self._with_interaction_cursor({"postId": post_id}, cursor)
        cursor_obj = (
            self.reposts.find(query).sort([("createdAt", -1), ("_id", -1)]).limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

    async def get_post_likes(
        self, post_id: str, limit: int = 20, cursor: Optional[dict] = None
    ) -> List[dict]:
        """Like rows for a post, newest first."""
        query = self._with_interaction_cursor({"postId": post_id}, cursor)
        cursor_obj = (
            self.likes.find(query).sort([("createdAt", -1), ("_id", -1)]).limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

    # Follows
    async def insert_follow(
        self, follower_id: str, following_id: str, status: str = "accepted"
    ):
        return await self.follows.insert_one(
            {
                "followerId": follower_id,
                "followingId": following_id,
                "status": status,
                "createdAt": datetime.now(timezone.utc),
            }
        )

    async def delete_follow(self, follower_id: str, following_id: str):
        return await self.follows.delete_one(
            {"followerId": follower_id, "followingId": following_id}
        )

    async def get_follow(self, follower_id: str, following_id: str) -> Optional[dict]:
        return await self.follows.find_one(
            {"followerId": follower_id, "followingId": following_id}
        )

    async def update_follow_status(
        self, follower_id: str, following_id: str, status: str
    ):
        return await self.follows.update_one(
            {"followerId": follower_id, "followingId": following_id},
            {"$set": {"status": status}},
        )

    async def get_following_ids(self, follower_id: str) -> List[str]:
        """Accepted follows only; a pending request grants nothing."""
        cursor = self.follows.find(
            {"followerId": follower_id, **ACCEPTED_FOLLOW}, {"followingId": 1}
        )
        rows = await cursor.to_list(length=None)
        return [row["followingId"] for row in rows]

    async def count_followers(self, user_id: str) -> int:
        return await self.follows.count_documents(
            {"followingId": user_id, **ACCEPTED_FOLLOW}
        )

    async def count_following(self, follower_id: str) -> int:
        return await self.follows.count_documents(
            {"followerId": follower_id, **ACCEPTED_FOLLOW}
        )

    async def get_followed_ids(
        self, follower_id: str, user_ids: List[str]
    ) -> List[str]:
        """Which of `user_ids` this user already follows (for the follow buttons)."""
        if not user_ids:
            return []
        cursor = self.follows.find(
            {
                "followerId": follower_id,
                "followingId": {"$in": user_ids},
                **ACCEPTED_FOLLOW,
            },
            {"followingId": 1},
        )
        rows = await cursor.to_list(length=None)
        return [row["followingId"] for row in rows]

    async def get_pending_follow_ids(
        self, follower_id: str, user_ids: List[str]
    ) -> List[str]:
        """Which of `user_ids` this user has a pending request to."""
        if not user_ids:
            return []
        cursor = self.follows.find(
            {
                "followerId": follower_id,
                "followingId": {"$in": user_ids},
                "status": "pending",
            },
            {"followingId": 1},
        )
        rows = await cursor.to_list(length=None)
        return [row["followingId"] for row in rows]

    async def get_follow_edges(
        self,
        match_field: str,
        user_id: str,
        limit: int = 20,
        cursor: Optional[dict] = None,
    ) -> List[dict]:
        """Follow rows where `match_field` (followingId or followerId) is the user.

        Pending requests stay out: neither list shows them until accepted.
        """
        query: dict = {match_field: user_id, **ACCEPTED_FOLLOW}
        if cursor:
            cursor_id = cursor.get("_id")
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
            self.follows.find(query).sort([("createdAt", -1), ("_id", -1)]).limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

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
    ) -> Dict[str, Dict[str, object]]:
        """Batch get user interactions for a list of posts."""
        if not post_ids or not user_id:
            return {
                pid: {
                    "isLiked": False,
                    "isBookmarked": False,
                    "isReposted": False,
                    "pollOptionId": None,
                }
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
        poll_votes = await self.poll_votes.find(
            {"userId": user_id, "postId": {"$in": post_ids}}
        ).to_list(length=None)

        liked_set = {l["postId"] for l in likes}
        bookmarked_set = {b["postId"] for b in bookmarks}
        reposted_set = {r["postId"] for r in reposts}
        poll_option_map = {v["postId"]: v["optionId"] for v in poll_votes}

        result = {}
        for pid in post_ids:
            result[pid] = {
                "isLiked": pid in liked_set,
                "isBookmarked": pid in bookmarked_set,
                "isReposted": pid in reposted_set,
                "pollOptionId": poll_option_map.get(pid),
            }
        return result

    # Poll votes
    async def get_poll_vote(self, post_id: str, user_id: str) -> Optional[dict]:
        return await self.poll_votes.find_one({"postId": post_id, "userId": user_id})

    async def insert_poll_vote(self, post_id: str, user_id: str, option_id: str):
        return await self.poll_votes.insert_one(
            {
                "postId": post_id,
                "userId": user_id,
                "optionId": option_id,
                "createdAt": datetime.now(timezone.utc),
            }
        )

    async def delete_poll_votes(self, post_id: str):
        return await self.poll_votes.delete_many({"postId": post_id})

    async def count_poll_votes(self, post_ids: List[str]) -> Dict[str, Dict[str, int]]:
        """Count votes per option for the given posts, in a single query.

        Returns `{postId: {optionId: votes}}`; this is the source of truth for
        poll results (nothing is denormalized on the post document).
        """
        if not post_ids:
            return {}

        pipeline = [
            {"$match": {"postId": {"$in": post_ids}}},
            {
                "$group": {
                    "_id": {"postId": "$postId", "optionId": "$optionId"},
                    "votes": {"$sum": 1},
                }
            },
        ]
        cursor = self.poll_votes.aggregate(pipeline)
        rows = await cursor.to_list(length=None)

        counts: Dict[str, Dict[str, int]] = {}
        for row in rows:
            key = row["_id"]
            counts.setdefault(key["postId"], {})[key["optionId"]] = row["votes"]
        return counts

    # Notifications
    async def upsert_notification(self, notification: dict, dedupe_key: Optional[str]):
        """Insert a notification, or leave an existing one with the same key alone.

        Toggleable actions (like/repost/follow) repeat all the time; the sparse
        unique index on `dedupeKey` plus `$setOnInsert` keep exactly one row.
        """
        if not dedupe_key:
            return await self.notifications.insert_one(notification)

        return await self.notifications.update_one(
            {"dedupeKey": dedupe_key},
            {"$setOnInsert": {**notification, "dedupeKey": dedupe_key}},
            upsert=True,
        )

    async def get_notification_post_previews(
        self, post_ids: List[str], visibility: Optional[dict] = None
    ) -> List[dict]:
        """Only the fields a notification snippet shows, in one projection."""
        if not post_ids:
            return []
        query: dict = {"postId": {"$in": post_ids}}
        if visibility:
            query = {"$and": [query, visibility]}
        cursor = self.posts.find(
            query,
            {"_id": 0, "postId": 1, "content": 1, "createdAt": 1},
        )
        return await cursor.to_list(length=None)

    async def prune_notifications(self, recipient_id: str, keep: int) -> None:
        """Drop a recipient's oldest notifications once the cap is exceeded."""
        total = await self.notifications.count_documents(
            {"recipientUserId": recipient_id}
        )
        if total <= keep:
            return

        cursor = (
            self.notifications.find({"recipientUserId": recipient_id}, {"_id": 1})
            .sort([("createdAt", -1), ("notificationId", -1)])
            .skip(keep)
        )
        stale = await cursor.to_list(length=None)
        if stale:
            await self.notifications.delete_many(
                {"_id": {"$in": [row["_id"] for row in stale]}}
            )

    async def delete_notifications(self, recipient_id: str, actor_id: str, types: List[str]) -> int:
        """Drop a recipient's notifications of the given types from one actor.

        A follow request that was accepted or declined must disappear from the
        Follows tab, and cancelling a request has the same effect.
        """
        result = await self.notifications.delete_many(
            {
                "recipientUserId": recipient_id,
                "actorUserId": actor_id,
                "type": {"$in": types},
            }
        )
        return result.deleted_count

    async def get_notifications(
        self,
        recipient_id: str,
        limit: int = 20,
        cursor: Optional[dict] = None,
        types: Optional[List[str]] = None,
    ) -> List[dict]:
        conditions: List[dict] = [{"recipientUserId": recipient_id}]
        if types:
            conditions.append({"type": {"$in": types}})

        if cursor:
            conditions.append(
                {
                    "$or": [
                        {"createdAt": {"$lt": cursor["createdAt"]}},
                        {
                            "createdAt": cursor["createdAt"],
                            "notificationId": {"$lt": cursor["notificationId"]},
                        },
                    ]
                }
            )

        cursor_obj = (
            self.notifications.find({"$and": conditions})
            .sort([("createdAt", -1), ("notificationId", -1)])
            .limit(limit)
        )
        return await cursor_obj.to_list(length=limit)

    async def count_unread_notifications_by_type(
        self, recipient_id: str, hidden_actor_ids: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """Unread notifications grouped by type, in one aggregation.

        Actors hidden from the recipient (blocked, or locked and not followed)
        are left out, so a badge can never count a row the list will not show.
        """
        match: dict = {"recipientUserId": recipient_id, "readAt": None}
        if hidden_actor_ids:
            match["actorUserId"] = {"$nin": hidden_actor_ids}
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
        ]
        cursor = self.notifications.aggregate(pipeline)
        rows = await cursor.to_list(length=None)
        return {row["_id"]: row["count"] for row in rows}

    async def mark_notifications_read(
        self, recipient_id: str, types: List[str], read_at
    ) -> int:
        """Stamp the recipient's unread notifications of the given types as read."""
        result = await self.notifications.update_many(
            {
                "recipientUserId": recipient_id,
                "readAt": None,
                "type": {"$in": types},
            },
            {"$set": {"readAt": read_at}},
        )
        return result.modified_count

    # Blocks and mutes
    async def insert_block(self, blocker_id: str, blocked_id: str):
        return await self.blocks.insert_one(
            {
                "blockerId": blocker_id,
                "blockedId": blocked_id,
                "createdAt": datetime.now(timezone.utc),
            }
        )

    async def delete_block(self, blocker_id: str, blocked_id: str):
        return await self.blocks.delete_one(
            {"blockerId": blocker_id, "blockedId": blocked_id}
        )

    async def get_block(self, blocker_id: str, blocked_id: str) -> Optional[dict]:
        return await self.blocks.find_one(
            {"blockerId": blocker_id, "blockedId": blocked_id}
        )

    async def get_blocked_ids(self, viewer_id: str) -> List[str]:
        """Who the viewer blocked, plus who blocked the viewer: block is mutual."""
        rows = await self.blocks.find(
            {"$or": [{"blockerId": viewer_id}, {"blockedId": viewer_id}]},
            {"blockerId": 1, "blockedId": 1},
        ).to_list(length=RELATION_SCAN_LIMIT)
        return [
            row["blockedId"] if row["blockerId"] == viewer_id else row["blockerId"]
            for row in rows
        ]

    async def get_blocked_users(
        self, blocker_id: str, limit: int = 20, cursor: Optional[dict] = None
    ) -> List[dict]:
        """Accounts the viewer blocked, newest first, shaped like an edge row."""
        query = self._with_interaction_cursor({"blockerId": blocker_id}, cursor)
        rows = (
            await self.blocks.find(query)
            .sort([("createdAt", -1), ("_id", -1)])
            .limit(limit)
            .to_list(length=limit)
        )
        return [self._edge_row(row["blockedId"], row) for row in rows]

    async def insert_mute(self, muter_id: str, muted_id: str):
        return await self.mutes.insert_one(
            {
                "muterId": muter_id,
                "mutedId": muted_id,
                "createdAt": datetime.now(timezone.utc),
            }
        )

    async def delete_mute(self, muter_id: str, muted_id: str):
        return await self.mutes.delete_one(
            {"muterId": muter_id, "mutedId": muted_id}
        )

    async def get_mute(self, muter_id: str, muted_id: str) -> Optional[dict]:
        return await self.mutes.find_one({"muterId": muter_id, "mutedId": muted_id})

    async def get_muted_ids(self, muter_id: str) -> List[str]:
        """Who the viewer muted. Unlike block, this is one-directional."""
        rows = await self.mutes.find(
            {"muterId": muter_id}, {"mutedId": 1}
        ).to_list(length=RELATION_SCAN_LIMIT)
        return [row["mutedId"] for row in rows]

    async def get_muted_users(
        self, muter_id: str, limit: int = 20, cursor: Optional[dict] = None
    ) -> List[dict]:
        query = self._with_interaction_cursor({"muterId": muter_id}, cursor)
        rows = (
            await self.mutes.find(query)
            .sort([("createdAt", -1), ("_id", -1)])
            .limit(limit)
            .to_list(length=limit)
        )
        return [self._edge_row(row["mutedId"], row) for row in rows]

    @staticmethod
    def _edge_row(user_id: str, row: dict) -> dict:
        """Shape a block/mute edge like an interaction row, for the user builders."""
        return {
            "userId": user_id,
            "createdAt": row["createdAt"],
            "_id": row["_id"],
        }
