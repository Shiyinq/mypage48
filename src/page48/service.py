import re
import uuid
from datetime import datetime
from typing import Optional, List

from src.auth.schemas import UserCurrent
from src.config import Settings
from src.infrastructure import AsyncBackgroundRunner
from src.logging_config import create_logger
from src.page48.constants import Info
from src.page48.exceptions import (
    PostCreationError,
    PostNotFoundError,
    UnauthorizedActionError,
    UserProfileNotFoundError,
)
from src.page48.repository import Page48Repository
from src.page48.schemas import (
    CreatePostRequest,
    EditPostRequest,
    Page48Image,
    Page48UserProfileResponse,
    PostPaginationMeta,
    PostPaginationResponse,
    PostResponse,
    ThreadResponse,
    ToggleResponse,
    TrendingTag,
    TrendingTagsResponse,
)
from src.storage.service import StorageService
from src.users.repository import UserRepository

logger = create_logger("page48_service", __name__)

TAG_PATTERN = re.compile(r"#(\w+)", re.UNICODE)
MAX_TAGS = 10
MAX_TAG_LENGTH = 50


class Page48Service:
    def __init__(
        self,
        repository: Page48Repository,
        background_tasks: AsyncBackgroundRunner,
        config: Settings,
        storage_service: StorageService,
        user_repository: UserRepository,
    ):
        self.repository = repository
        self.background_tasks = background_tasks
        self.config = config
        self.storage_service = storage_service
        self.user_repository = user_repository

    async def _resolve_author_avatar(
        self, post: dict, user_map: Optional[dict], cache: dict
    ) -> tuple[Optional[str], Optional[str]]:
        """Resolve the author's *current* avatar (by userId), cached per request.

        Posts store the avatar path at creation time, which becomes stale if the
        user later changes or removes their picture, so we prefer the live user
        document and fall back to the value stored on the post.
        """
        user_id = post.get("userId")
        cache_key = user_id or post.get("postId")
        if cache_key in cache:
            return cache[cache_key]

        user_doc = None
        if user_id:
            if user_map is not None:
                user_doc = user_map.get(user_id)
            else:
                users = await self.user_repository.get_users_by_ids([user_id])
                user_doc = users[0] if users else None

        raw = user_doc.get("profilePicture") if user_doc else None
        if not raw:
            raw = post.get("userProfilePicture")

        picture = None
        picture_small = None
        if raw:
            try:
                picture = await self.storage_service.resolve_url(raw)
                picture_small = await self.storage_service.resolve_url(
                    raw, variant="small"
                )
            except Exception as e:
                logger.error(
                    f"Failed to resolve avatar for post {post.get('postId')}: {str(e)}"
                )

        result = (picture, picture_small)
        cache[cache_key] = result
        return result

    async def _enrich_post(
        self,
        post: dict,
        user_interactions: dict = None,
        avatar_cache: dict = None,
        user_map: Optional[dict] = None,
    ) -> PostResponse:
        """Helper to format a raw db dict into PostResponse."""
        if not user_interactions:
            user_interactions = {}
        if avatar_cache is None:
            avatar_cache = {}

        interactions = user_interactions.get(post["postId"], {})

        user_picture, user_picture_small = await self._resolve_author_avatar(
            post, user_map, avatar_cache
        )
        
        # Resolve image variants
        images = []
        for img in post.get("images", []):
            try:
                filename = img["filename"]
                variants = await self.storage_service.resolve_image_variants(
                    filename, default_blur_hash=img.get("blurHash")
                )
                images.append(
                    Page48Image(
                        filename=filename,
                        url=variants["url"],
                        url_medium=variants["url_medium"],
                        url_small=variants["url_small"],
                        blurHash=variants.get("blurHash") or img.get("blurHash"),
                        width=img.get("width", 0),
                        height=img.get("height", 0),
                    )
                )
            except Exception as e:
                logger.error(f"Failed to resolve image {img.get('filename')}: {str(e)}")

        return PostResponse(
            postId=post["postId"],
            rootPostId=post.get("rootPostId"),
            parentPostId=post.get("parentPostId"),
            depth=post.get("depth", 0),
            replyCount=post.get("replyCount", 0),
            
            userId=post["userId"],
            username=post["username"],
            userDisplayName=post["userDisplayName"],
            userProfilePicture=user_picture,
            userProfilePicture_small=user_picture_small,
            userBlurHash=post.get("userBlurHash"),
            
            content=post["content"],
            images=images,
            tags=post.get("tags", []),
            
            likesCount=post.get("likesCount", 0),
            repostCount=post.get("repostCount", 0),
            bookmarksCount=post.get("bookmarksCount", 0),
            
            isEdited=post.get("isEdited", False),
            createdAt=post["createdAt"],
            updatedAt=post["updatedAt"],
            
            isLiked=interactions.get("isLiked", False),
            isReposted=interactions.get("isReposted", False),
            isBookmarked=interactions.get("isBookmarked", False),
        )

    async def _enrich_posts(self, posts: List[dict], user_id: Optional[str] = None) -> List[PostResponse]:
        if not posts:
            return []
            
        post_ids = [p["postId"] for p in posts]
        interactions = {}
        if user_id:
            interactions = await self.repository.get_user_interactions(post_ids, user_id)

        author_ids = list({p["userId"] for p in posts if p.get("userId")})
        users = await self.user_repository.get_users_by_ids(author_ids)
        user_map = {u["userId"]: u for u in users}

        enriched = []
        avatar_cache = {}
        for p in posts:
            enriched.append(
                await self._enrich_post(p, interactions, avatar_cache, user_map)
            )

        return enriched

    def _extract_tags(self, content: str, explicit: Optional[List[str]] = None) -> List[str]:
        """Collect hashtags from the content plus any explicitly provided tags."""
        tags: List[str] = []

        def add(raw: str) -> None:
            normalized = str(raw).strip().lstrip("#").lower()[:MAX_TAG_LENGTH]
            if normalized and normalized not in tags:
                tags.append(normalized)

        for match in TAG_PATTERN.findall(content or ""):
            add(match)
        for tag in explicit or []:
            add(tag)

        return tags[:MAX_TAGS]

    async def get_trending_tags(self, limit: int = 10) -> TrendingTagsResponse:
        rows = await self.repository.get_trending_tags(limit)
        return TrendingTagsResponse(
            tags=[TrendingTag(tag=row["_id"], count=row["count"]) for row in rows]
        )

    async def get_posts_by_tag(
        self,
        tag: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        user_id: Optional[str] = None,
        media: Optional[str] = None,
    ) -> PostPaginationResponse:
        normalized = tag.strip().lstrip("#").lower()

        cursor_dict = None
        if cursor:
            try:
                parts = cursor.split("_")
                cursor_dict = {
                    "createdAt": datetime.fromisoformat(parts[0]),
                    "postId": parts[1],
                }
            except Exception:
                pass

        posts = await self.repository.get_posts_by_tag(
            normalized, limit + 1, cursor_dict, media
        )

        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]

        enriched_posts = await self._enrich_posts(posts, user_id)

        next_cursor = None
        if has_more and enriched_posts:
            last_post = posts[-1]
            next_cursor = f"{last_post['createdAt'].isoformat()}_{last_post['postId']}"

        return PostPaginationResponse(
            data=enriched_posts,
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more),
        )

    async def create_post(self, data: CreatePostRequest, user: UserCurrent) -> PostResponse:
        try:
            post_id = str(uuid.uuid4())
            now = datetime.now()
            
            root_post_id = None
            depth = 0
            
            if data.parentPostId:
                parent = await self.repository.get_post_by_id(data.parentPostId)
                if not parent:
                    raise PostNotFoundError()
                    
                root_post_id = parent.get("rootPostId") or data.parentPostId
                depth = parent.get("depth", 0) + 1
                
                # Update reply count of parent
                await self.repository.increment_post_stats(data.parentPostId, "replyCount", 1)

            images_data = [{"filename": fn} for fn in data.images]
            tags = self._extract_tags(data.content, data.tags)

            post_data = {
                "postId": post_id,
                "rootPostId": root_post_id,
                "parentPostId": data.parentPostId,
                "depth": depth,
                "replyCount": 0,
                
                "userId": user.userId,
                "username": user.username,
                "userDisplayName": user.name,
                "userProfilePicture": user.profilePicture,
                "userProfilePicture_small": user.profilePicture_small,
                "userBlurHash": user.blurHash,
                
                "content": data.content,
                "images": images_data,
                "tags": tags,
                
                "likesCount": 0,
                "repostCount": 0,
                "bookmarksCount": 0,
                
                "isEdited": False,
                "createdAt": now,
                "updatedAt": now,
            }
            
            await self.repository.insert_post(post_data)
            
            # Enrich and return
            return await self._enrich_post(post_data)
            
        except PostNotFoundError:
            raise
        except Exception as e:
            logger.exception(f"Error creating post: {str(e)}")
            raise PostCreationError()

    async def get_feed(
        self,
        limit: int = 20,
        cursor: Optional[str] = None,
        user_id: Optional[str] = None,
        media: Optional[str] = None,
    ) -> PostPaginationResponse:
        cursor_dict = None
        if cursor:
            try:
                parts = cursor.split("_")
                cursor_dict = {
                    "createdAt": datetime.fromisoformat(parts[0]),
                    "postId": parts[1],
                }
            except Exception:
                pass

        posts = await self.repository.get_feed(limit + 1, cursor_dict, media)
        
        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]
            
        enriched_posts = await self._enrich_posts(posts, user_id)
        
        next_cursor = None
        if has_more and enriched_posts:
            last_post = posts[-1]
            next_cursor = f"{last_post['createdAt'].isoformat()}_{last_post['postId']}"
            
        return PostPaginationResponse(
            data=enriched_posts,
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more)
        )

    async def get_post(self, post_id: str, user_id: Optional[str] = None) -> PostResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
            
        enriched_posts = await self._enrich_posts([post], user_id)
        return enriched_posts[0]

    async def _build_thread_tree(self, post_id: str, posts_by_parent: dict, enriched_dict: dict) -> ThreadResponse:
        post = enriched_dict[post_id]
        replies = []
        
        for reply_id in posts_by_parent.get(post_id, []):
            replies.append(await self._build_thread_tree(reply_id, posts_by_parent, enriched_dict))
            
        return ThreadResponse(post=post, replies=replies)

    async def get_thread(self, post_id: str, user_id: Optional[str] = None) -> ThreadResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
            
        root_id = post.get("rootPostId") or post_id
        
        # Get all posts in this thread (root + all replies)
        if root_id == post_id:
            all_raw = [post]
        else:
            root_post = await self.repository.get_post_by_id(root_id)
            all_raw = [root_post] if root_post else []
            
        replies_raw = await self.repository.get_thread_replies(root_id)
        
        raw_dict = {p["postId"]: p for p in all_raw + replies_raw}
        if post_id not in raw_dict:
            raw_dict[post_id] = post
            
        all_unique = list(raw_dict.values())
        enriched = await self._enrich_posts(all_unique, user_id)
        
        enriched_dict = {p.postId: p for p in enriched}
        
        posts_by_parent = {}
        for p in all_unique:
            pid = p.get("parentPostId")
            if pid:
                if pid not in posts_by_parent:
                    posts_by_parent[pid] = []
                posts_by_parent[pid].append(p["postId"])
                
        return await self._build_thread_tree(root_id, posts_by_parent, enriched_dict)

    async def get_direct_replies(self, post_id: str, limit: int = 20, cursor: Optional[str] = None, user_id: Optional[str] = None) -> PostPaginationResponse:
        cursor_dict = None
        if cursor:
            try:
                parts = cursor.split("_")
                cursor_dict = {
                    "createdAt": datetime.fromisoformat(parts[0]),
                    "postId": parts[1]
                }
            except Exception:
                pass

        posts = await self.repository.get_direct_replies(post_id, limit + 1, cursor_dict)
        
        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]
            
        enriched_posts = await self._enrich_posts(posts, user_id)
        
        next_cursor = None
        if has_more and enriched_posts:
            last_post = posts[-1]
            next_cursor = f"{last_post['createdAt'].isoformat()}_{last_post['postId']}"
            
        return PostPaginationResponse(
            data=enriched_posts,
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more)
        )

    async def toggle_like(self, post_id: str, user_id: str) -> ToggleResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
            
        existing = await self.repository.get_like(post_id, user_id)
        if existing:
            await self.repository.delete_like(post_id, user_id)
            await self.repository.increment_post_stats(post_id, "likesCount", -1)
            new_status = False
            new_count = max(0, post.get("likesCount", 0) - 1)
        else:
            await self.repository.insert_like(post_id, user_id)
            await self.repository.increment_post_stats(post_id, "likesCount", 1)
            new_status = True
            new_count = post.get("likesCount", 0) + 1
            
        return ToggleResponse(status=new_status, count=new_count)

    async def toggle_repost(self, post_id: str, user_id: str) -> ToggleResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
            
        existing = await self.repository.get_repost(post_id, user_id)
        if existing:
            await self.repository.delete_repost(post_id, user_id)
            await self.repository.increment_post_stats(post_id, "repostCount", -1)
            new_status = False
            new_count = max(0, post.get("repostCount", 0) - 1)
        else:
            await self.repository.insert_repost(post_id, user_id)
            await self.repository.increment_post_stats(post_id, "repostCount", 1)
            new_status = True
            new_count = post.get("repostCount", 0) + 1
            
        return ToggleResponse(status=new_status, count=new_count)

    async def toggle_bookmark(self, post_id: str, user_id: str) -> ToggleResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
            
        existing = await self.repository.get_bookmark(post_id, user_id)
        if existing:
            await self.repository.delete_bookmark(post_id, user_id)
            await self.repository.increment_post_stats(post_id, "bookmarksCount", -1)
            new_status = False
            new_count = max(0, post.get("bookmarksCount", 0) - 1)
        else:
            await self.repository.insert_bookmark(post_id, user_id)
            await self.repository.increment_post_stats(post_id, "bookmarksCount", 1)
            new_status = True
            new_count = post.get("bookmarksCount", 0) + 1
            
        return ToggleResponse(status=new_status, count=new_count)
        
    async def delete_post(self, post_id: str, user_id: str, is_admin: bool = False):
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
            
        if not is_admin and post["userId"] != user_id:
            raise UnauthorizedActionError()
            
        await self.repository.delete_post(post_id)
        
        if post.get("parentPostId"):
            await self.repository.increment_post_stats(post["parentPostId"], "replyCount", -1)

    async def get_user_posts(
        self,
        target_username: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        current_user_id: Optional[str] = None,
        media: Optional[str] = None,
    ) -> PostPaginationResponse:
        cursor_dict = None
        if cursor:
            try:
                parts = cursor.split("_")
                cursor_dict = {
                    "createdAt": datetime.fromisoformat(parts[0]),
                    "postId": parts[1],
                }
            except Exception:
                pass

        posts = await self.repository.get_user_posts(
            target_username, limit + 1, cursor_dict, media
        )
        
        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]
            
        enriched_posts = await self._enrich_posts(posts, current_user_id)
        
        next_cursor = None
        if has_more and enriched_posts:
            last_post = posts[-1]
            next_cursor = f"{last_post['createdAt'].isoformat()}_{last_post['postId']}"
            
        return PostPaginationResponse(
            data=enriched_posts,
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more)
        )

    async def get_user_replies(self, target_username: str, limit: int = 20, cursor: Optional[str] = None, current_user_id: Optional[str] = None) -> PostPaginationResponse:
        cursor_dict = None
        if cursor:
            try:
                parts = cursor.split("_")
                cursor_dict = {
                    "createdAt": datetime.fromisoformat(parts[0]),
                    "postId": parts[1]
                }
            except Exception:
                pass

        posts = await self.repository.get_user_replies(target_username, limit + 1, cursor_dict)
        
        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]
            
        enriched_posts = await self._enrich_posts(posts, current_user_id)
        
        next_cursor = None
        if has_more and enriched_posts:
            last_post = posts[-1]
            next_cursor = f"{last_post['createdAt'].isoformat()}_{last_post['postId']}"
            
        return PostPaginationResponse(
            data=enriched_posts,
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more)
        )

    async def get_user_bookmarks(self, user_id: str, limit: int = 20, cursor: Optional[str] = None) -> PostPaginationResponse:
        cursor_dict = None
        if cursor:
            try:
                parts = cursor.split("_")
                cursor_dict = {
                    "createdAt": datetime.fromisoformat(parts[0]),
                    "_id": parts[1] # Need ObjectId for bookmark pagination
                }
            except Exception:
                pass

        result = await self.repository.get_user_bookmarks(user_id, limit + 1, cursor_dict)
        bookmarks = result["bookmarks"]
        posts_by_id = {p["postId"]: p for p in result["posts"]}
        
        has_more = len(bookmarks) > limit
        if has_more:
            bookmarks = bookmarks[:limit]
            
        ordered_posts = [posts_by_id[b["postId"]] for b in bookmarks if b["postId"] in posts_by_id]
        enriched_posts = await self._enrich_posts(ordered_posts, user_id)
        
        next_cursor = None
        if has_more and bookmarks:
            last_b = bookmarks[-1]
            next_cursor = f"{last_b['createdAt'].isoformat()}_{str(last_b['_id'])}"
            
        return PostPaginationResponse(
            data=enriched_posts,
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more)
        )

    async def get_user_likes(
        self, user_id: str, limit: int = 20, cursor: Optional[str] = None
    ) -> PostPaginationResponse:
        cursor_dict = None
        if cursor:
            try:
                parts = cursor.split("_")
                cursor_dict = {
                    "createdAt": datetime.fromisoformat(parts[0]),
                    "_id": parts[1],  # ObjectId used for like pagination
                }
            except Exception:
                pass

        result = await self.repository.get_user_likes(user_id, limit + 1, cursor_dict)
        likes = result["likes"]
        posts_by_id = {p["postId"]: p for p in result["posts"]}

        has_more = len(likes) > limit
        if has_more:
            likes = likes[:limit]

        ordered_posts = [
            posts_by_id[like["postId"]]
            for like in likes
            if like["postId"] in posts_by_id
        ]
        enriched_posts = await self._enrich_posts(ordered_posts, user_id)

        next_cursor = None
        if has_more and likes:
            last_l = likes[-1]
            next_cursor = f"{last_l['createdAt'].isoformat()}_{str(last_l['_id'])}"

        return PostPaginationResponse(
            data=enriched_posts,
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more),
        )

    async def get_user_profile(self, username: str) -> Page48UserProfileResponse:
        user = await self.user_repository.find_one({"username": username.lower()})
        if not user:
            raise UserProfileNotFoundError()

        stored_username = user.get("username", username)

        raw_picture = user.get("profilePicture")
        profile_picture = None
        profile_picture_medium = None
        profile_picture_small = None
        blur_hash = user.get("blurHash")

        if raw_picture:
            try:
                profile_picture = await self.storage_service.resolve_url(raw_picture)
                profile_picture_medium = await self.storage_service.resolve_url(
                    raw_picture, variant="medium"
                )
                profile_picture_small = await self.storage_service.resolve_url(
                    raw_picture, variant="small"
                )
            except Exception as e:
                logger.error(
                    f"Failed to resolve profile picture for {username}: {str(e)}"
                )

        post_count = await self.repository.count_user_posts(stored_username)
        repost_count = await self.repository.count_user_reposts(
            user.get("userId", "")
        )

        return Page48UserProfileResponse(
            userId=user.get("userId", ""),
            name=user.get("name") or stored_username,
            username=stored_username,
            bio=user.get("bio"),
            profilePicture=profile_picture,
            profilePicture_medium=profile_picture_medium,
            profilePicture_small=profile_picture_small,
            blurHash=blur_hash,
            postCount=post_count,
            repostCount=repost_count,
        )

    async def get_user_reposts(
        self,
        username: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        current_user_id: Optional[str] = None,
    ) -> PostPaginationResponse:
        user = await self.user_repository.find_one({"username": username.lower()})
        if not user:
            raise UserProfileNotFoundError()

        cursor_dict = None
        if cursor:
            try:
                parts = cursor.split("_")
                cursor_dict = {
                    "createdAt": datetime.fromisoformat(parts[0]),
                    "_id": parts[1],  # ObjectId used for repost pagination
                }
            except Exception:
                pass

        result = await self.repository.get_user_reposts(
            user["userId"], limit + 1, cursor_dict
        )
        reposts = result["reposts"]
        posts_by_id = {p["postId"]: p for p in result["posts"]}

        has_more = len(reposts) > limit
        if has_more:
            reposts = reposts[:limit]

        ordered_posts = [
            posts_by_id[r["postId"]] for r in reposts if r["postId"] in posts_by_id
        ]
        enriched_posts = await self._enrich_posts(ordered_posts, current_user_id)

        reposted_at = {r["postId"]: r.get("createdAt") for r in reposts}
        for post in enriched_posts:
            post.repostedAt = reposted_at.get(post.postId)

        next_cursor = None
        if has_more and reposts:
            last_r = reposts[-1]
            next_cursor = f"{last_r['createdAt'].isoformat()}_{str(last_r['_id'])}"

        return PostPaginationResponse(
            data=enriched_posts,
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more),
        )
