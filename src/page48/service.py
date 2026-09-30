import re
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from pymongo.errors import DuplicateKeyError

from src.auth.schemas import UserCurrent
from src.config import Settings
from src.infrastructure import AsyncBackgroundRunner
from src.logging_config import create_logger
from src.page48.exceptions import (
    CannotReportSelfError,
    InvalidPollOptionError,
    InvalidPollOptionsError,
    InvalidReportTargetError,
    InvalidVideoError,
    InvalidVideoTypeError,
    MaxVideoExceededError,
    MediaConflictError,
    PollAlreadyVotedError,
    PollEndedError,
    PollMediaConflictError,
    PollNotFoundError,
    PollReplyNotAllowedError,
    PostCreationError,
    PostNotFoundError,
    ReportAlreadyExistsError,
    ReportCreationError,
    UnauthorizedActionError,
    UserProfileNotFoundError,
    VideoTooLargeError,
    VideoUploadError,
)
from src.page48.repository import Page48Repository
from src.page48.schemas import (
    ActiveUserItem,
    ActiveUsersResponse,
    AdminReportItem,
    AdminReportPaginationMeta,
    AdminReportPaginationResponse,
    CreatePostRequest,
    EditPostRequest,
    Page48Image,
    Page48UserProfileResponse,
    Page48Video,
    PollOptionResponse,
    PollResponse,
    PostPaginationMeta,
    PostPaginationResponse,
    PostResponse,
    ReportCreate,
    ReportResponse,
    ThreadResponse,
    ToggleResponse,
    TrendingTag,
    TrendingTagsResponse,
    VideoUploadResponse,
)
from src.storage.service import StorageService
from src.users.repository import UserRepository

logger = create_logger("page48_service", __name__)

TAG_PATTERN = re.compile(r"#(\w+)", re.UNICODE)
MAX_TAGS = 10
MAX_TAG_LENGTH = 50
POLL_DURATION_HOURS = 24
MIN_POLL_OPTIONS = 2
MAX_POLL_OPTIONS = 6
MAX_POLL_OPTION_LENGTH = 50
ALLOWED_VIDEO_TYPES = {
    "video/mp4": "mp4",
    "video/webm": "webm",
}


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
        poll_counts: Optional[dict] = None,
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

        # Resolve videos (direct presigned URL so playback supports HTTP Range)
        videos = []
        for vid in post.get("videos", []):
            try:
                filename = vid["filename"]
                url = await self.storage_service.resolve_video_url(filename)
                videos.append(
                    Page48Video(
                        filename=filename,
                        url=url,
                        width=vid.get("width", 0),
                        height=vid.get("height", 0),
                        duration=vid.get("duration", 0) or 0.0,
                    )
                )
            except Exception as e:
                logger.error(f"Failed to resolve video {vid.get('filename')}: {str(e)}")

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
            videos=videos,
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
            poll=(
                self._build_poll_response(
                    post["poll"], poll_counts, interactions.get("pollOptionId")
                )
                if post.get("poll")
                else None
            ),
        )

    async def _enrich_posts(
        self, posts: List[dict], user_id: Optional[str] = None
    ) -> List[PostResponse]:
        if not posts:
            return []

        post_ids = [p["postId"] for p in posts]
        interactions = {}
        if user_id:
            interactions = await self.repository.get_user_interactions(
                post_ids, user_id
            )

        poll_post_ids = [p["postId"] for p in posts if p.get("poll")]
        poll_counts = await self.repository.count_poll_votes(poll_post_ids)

        author_ids = list({p["userId"] for p in posts if p.get("userId")})
        users = await self.user_repository.get_users_by_ids(author_ids)
        user_map = {u["userId"]: u for u in users}

        enriched = []
        avatar_cache = {}
        for p in posts:
            enriched.append(
                await self._enrich_post(
                    p,
                    interactions,
                    avatar_cache,
                    user_map,
                    poll_counts.get(p["postId"]),
                )
            )

        return enriched

    # Polls
    @staticmethod
    def _build_poll_options(raw_options: List[str]) -> List[dict]:
        """Validate the submitted option texts and number them."""
        options = [str(option).strip() for option in raw_options or []]
        if not MIN_POLL_OPTIONS <= len(options) <= MAX_POLL_OPTIONS:
            raise InvalidPollOptionsError()
        empty_or_too_long = any(
            not option or len(option) > MAX_POLL_OPTION_LENGTH for option in options
        )
        if empty_or_too_long:
            raise InvalidPollOptionsError()

        return [
            {"id": f"opt{index + 1}", "text": text}
            for index, text in enumerate(options)
        ]

    @staticmethod
    def _is_poll_expired(poll: dict, now: Optional[datetime] = None) -> bool:
        """A poll is over as soon as `endsAt` has passed; nothing has to be
        scheduled for that, it is derived on every read."""
        ends_at = poll.get("endsAt")
        if not ends_at:
            return False
        return (now or datetime.now()) >= ends_at

    def _build_poll_response(
        self,
        poll: dict,
        counts: Optional[dict] = None,
        my_option_id: Optional[str] = None,
    ) -> PollResponse:
        counts = counts or {}
        options = [
            PollOptionResponse(
                id=option["id"],
                text=option["text"],
                votes=counts.get(option["id"], 0),
            )
            for option in poll.get("options", [])
        ]

        return PollResponse(
            options=options,
            totalVotes=sum(option.votes for option in options),
            endsAt=poll["endsAt"],
            isExpired=self._is_poll_expired(poll),
            myOptionId=my_option_id,
        )

    def _extract_tags(
        self, content: str, explicit: Optional[List[str]] = None
    ) -> List[str]:
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

    async def get_active_users(
        self,
        limit: int = 5,
        days: int = 7,
        exclude_user_id: Optional[str] = None,
    ) -> ActiveUsersResponse:
        """Most active (most top-level posts) users in the last `days`."""
        since = datetime.now() - timedelta(days=days)
        # Fetch one extra row when we may need to drop the current user.
        rows = await self.repository.get_most_active_users(
            limit + 1 if exclude_user_id else limit, since
        )
        if exclude_user_id:
            rows = [row for row in rows if row["_id"] != exclude_user_id]
        rows = rows[:limit]

        user_ids = [row["_id"] for row in rows if row.get("_id")]
        users = await self.user_repository.get_users_by_ids(user_ids)
        user_map = {u["userId"]: u for u in users}

        picture_cache: dict = {}
        items: List[ActiveUserItem] = []
        for row in rows:
            user = user_map.get(row["_id"])
            picture = await self._resolve_picture(
                (user or {}).get("profilePicture"), picture_cache
            )
            items.append(
                ActiveUserItem(
                    userId=row["_id"],
                    username=(user or {}).get("username") or row.get("username") or "",
                    name=(user or {}).get("name") or row.get("name") or "",
                    profilePicture=picture,
                    postCount=row.get("postCount", 0),
                    lastPostedAt=row.get("lastPostedAt"),
                )
            )
        return ActiveUsersResponse(users=items)

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

    async def upload_video(
        self,
        user: UserCurrent,
        data: bytes,
        content_type: Optional[str],
        width: int = 0,
        height: int = 0,
        duration: float = 0.0,
    ) -> VideoUploadResponse:
        """Validate and store an uploaded video, returning its reference + URL."""
        if not data:
            raise InvalidVideoTypeError()
        if len(data) > self.config.max_page48_video_upload_size_bytes:
            raise VideoTooLargeError()

        extension = ALLOWED_VIDEO_TYPES.get((content_type or "").lower())
        if not extension:
            raise InvalidVideoTypeError()

        try:
            filename = f"page48/{user.userId}/{uuid.uuid4().hex}.{extension}"
            await self.storage_service.upload_object(
                data, filename, content_type or "video/mp4"
            )
            url = await self.storage_service.resolve_video_url(filename)
            return VideoUploadResponse(
                filename=filename,
                url=url,
                width=width or 0,
                height=height or 0,
                duration=duration or 0.0,
            )
        except (VideoTooLargeError, InvalidVideoTypeError):
            raise
        except Exception as e:
            logger.exception(f"Error uploading video: {str(e)}")
            raise VideoUploadError()

    async def create_post(
        self, data: CreatePostRequest, user: UserCurrent
    ) -> PostResponse:
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
                await self.repository.increment_post_stats(
                    data.parentPostId, "replyCount", 1
                )

            # Dimensions come from the client so the feed can reserve the right
            # box for each photo without cropping it.
            images_data = [
                {
                    "filename": ref.filename,
                    "width": ref.width or 0,
                    "height": ref.height or 0,
                }
                for ref in data.images
            ]
            video_refs = data.videos or []

            # A post is either images or a single video, never both.
            if images_data and video_refs:
                raise MediaConflictError()
            if len(video_refs) > 1:
                raise MaxVideoExceededError()

            videos_data = []
            for ref in video_refs:
                # The object must live under the uploader's own prefix.
                if not ref.filename.startswith(f"page48/{user.userId}/"):
                    raise InvalidVideoError()
                if not await self.storage_service.repository.file_exists(ref.filename):
                    raise InvalidVideoError()
                videos_data.append(
                    {
                        "filename": ref.filename,
                        "width": ref.width or 0,
                        "height": ref.height or 0,
                        "duration": ref.duration or 0.0,
                    }
                )

            tags = self._extract_tags(data.content, data.tags)

            poll_data = None
            if data.poll is not None:
                if images_data or videos_data:
                    raise PollMediaConflictError()
                if data.parentPostId:
                    raise PollReplyNotAllowedError()
                poll_data = {
                    "endsAt": now + timedelta(hours=POLL_DURATION_HOURS),
                    "options": self._build_poll_options(data.poll.options),
                }

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
                "videos": videos_data,
                "poll": poll_data,
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

        except (
            PostNotFoundError,
            MediaConflictError,
            MaxVideoExceededError,
            InvalidVideoError,
            InvalidPollOptionsError,
            PollMediaConflictError,
            PollReplyNotAllowedError,
        ):
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
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more),
        )

    async def get_post(
        self, post_id: str, user_id: Optional[str] = None
    ) -> PostResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()

        enriched_posts = await self._enrich_posts([post], user_id)
        return enriched_posts[0]

    async def _build_thread_tree(
        self, post_id: str, posts_by_parent: dict, enriched_dict: dict
    ) -> ThreadResponse:
        post = enriched_dict[post_id]
        replies = []

        for reply_id in posts_by_parent.get(post_id, []):
            replies.append(
                await self._build_thread_tree(reply_id, posts_by_parent, enriched_dict)
            )

        return ThreadResponse(post=post, replies=replies)

    async def get_thread(
        self, post_id: str, user_id: Optional[str] = None
    ) -> ThreadResponse:
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

    async def get_direct_replies(
        self,
        post_id: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        user_id: Optional[str] = None,
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

        posts = await self.repository.get_direct_replies(
            post_id, limit + 1, cursor_dict
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

    async def vote_poll(
        self, post_id: str, option_id: str, user_id: str
    ) -> PollResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()

        poll = post.get("poll")
        if not poll:
            raise PollNotFoundError()
        if self._is_poll_expired(poll):
            raise PollEndedError()

        valid_option_ids = {option["id"] for option in poll.get("options", [])}
        if option_id not in valid_option_ids:
            raise InvalidPollOptionError()

        if await self.repository.get_poll_vote(post_id, user_id):
            raise PollAlreadyVotedError()

        try:
            await self.repository.insert_poll_vote(post_id, user_id, option_id)
        except DuplicateKeyError:
            # Concurrent vote from the same user reached the unique index first.
            raise PollAlreadyVotedError()

        counts = await self.repository.count_poll_votes([post_id])
        return self._build_poll_response(poll, counts.get(post_id), option_id)

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

    async def edit_post(
        self, post_id: str, data: EditPostRequest, user_id: str
    ) -> PostResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()

        if post["userId"] != user_id:
            raise UnauthorizedActionError()

        tags = self._extract_tags(data.content, data.tags)
        await self.repository.update_post(
            post_id,
            {
                "content": data.content,
                "tags": tags,
                "isEdited": True,
                "updatedAt": datetime.now(),
            },
        )

        updated = await self.repository.get_post_by_id(post_id)
        enriched = await self._enrich_posts([updated], user_id)
        return enriched[0]

    async def create_report(
        self, data: ReportCreate, reporter: UserCurrent
    ) -> ReportResponse:
        try:
            owner_id = None
            if data.targetType == "post":
                target = await self.repository.get_post_by_id(data.targetId)
                if not target:
                    raise InvalidReportTargetError()
                owner_id = target.get("userId")
            else:
                target = await self.user_repository.find_one({"userId": data.targetId})
                if not target:
                    raise InvalidReportTargetError()
                owner_id = target.get("userId")

            if owner_id and owner_id == reporter.userId:
                raise CannotReportSelfError()

            existing = await self.repository.get_report(
                reporter.userId, data.targetType, data.targetId
            )
            if existing:
                raise ReportAlreadyExistsError()

            report_id = str(uuid.uuid4())
            now = datetime.now()
            report_data = {
                "reportId": report_id,
                "targetType": data.targetType,
                "targetId": data.targetId,
                "targetOwnerUserId": owner_id,
                "reporterUserId": reporter.userId,
                "reporterUsername": reporter.username,
                "reason": data.reason,
                "note": data.note,
                "status": "pending",
                "createdAt": now,
            }
            await self.repository.insert_report(report_data)

            return ReportResponse(
                reportId=report_id,
                targetType=data.targetType,
                targetId=data.targetId,
                reason=data.reason,
                note=data.note,
                status="pending",
                createdAt=now,
            )
        except (
            InvalidReportTargetError,
            CannotReportSelfError,
            ReportAlreadyExistsError,
        ):
            raise
        except Exception as e:
            logger.exception(f"Error creating report: {str(e)}")
            raise ReportCreationError()

    async def _resolve_picture(self, raw: Optional[str], cache: dict) -> Optional[str]:
        """Resolve a stored picture path to a small URL, cached per request."""
        if not raw:
            return None
        if raw in cache:
            return cache[raw]
        try:
            url = await self.storage_service.resolve_url(raw, variant="small")
        except Exception as e:
            logger.error(f"Failed to resolve report picture {raw}: {str(e)}")
            url = None
        cache[raw] = url
        return url

    async def _enrich_reports(self, reports: List[dict]) -> List[AdminReportItem]:
        """Attach target previews and reporter info to raw report documents."""
        if not reports:
            return []

        post_ids = [r["targetId"] for r in reports if r.get("targetType") == "post"]
        post_targets = await self.repository.get_posts_by_ids(post_ids)
        post_map = {p["postId"]: p for p in post_targets}

        user_ids: set = set()
        for r in reports:
            if r.get("reporterUserId"):
                user_ids.add(r["reporterUserId"])
            if r.get("targetType") == "user" and r.get("targetId"):
                user_ids.add(r["targetId"])
        for p in post_targets:
            if p.get("userId"):
                user_ids.add(p["userId"])

        users = await self.user_repository.get_users_by_ids(list(user_ids))
        user_map = {u["userId"]: u for u in users}

        avatar_cache: dict = {}
        items: List[AdminReportItem] = []
        for r in reports:
            target_type = r.get("targetType")
            if target_type not in ("post", "user"):
                target_type = "post"
            reason = r.get("reason")
            if reason not in ("spam", "harassment", "inappropriate", "other"):
                reason = "other"

            target_id = r.get("targetId", "")
            target_exists = True
            target_username = None
            target_display_name = None
            target_content = None
            target_image_count = 0
            target_picture = None

            if target_type == "post":
                post = post_map.get(target_id)
                if post:
                    target_content = post.get("content")
                    target_image_count = len(post.get("images") or [])
                    owner = user_map.get(post.get("userId"))
                    target_username = post.get("username")
                    target_display_name = (
                        owner.get("name") if owner else post.get("userDisplayName")
                    )
                    raw_picture = (
                        owner.get("profilePicture") if owner else None
                    ) or post.get("userProfilePicture")
                    target_picture = await self._resolve_picture(
                        raw_picture, avatar_cache
                    )
                else:
                    target_exists = False
            else:
                user = user_map.get(target_id)
                if user:
                    target_username = user.get("username")
                    target_display_name = user.get("name")
                    target_picture = await self._resolve_picture(
                        user.get("profilePicture"), avatar_cache
                    )
                else:
                    target_exists = False

            reporter = user_map.get(r.get("reporterUserId"))
            reporter_username = r.get("reporterUsername") or (
                reporter.get("username") if reporter else None
            )

            items.append(
                AdminReportItem(
                    reportId=r["reportId"],
                    targetType=target_type,
                    targetId=target_id,
                    reason=reason,
                    note=r.get("note"),
                    status=r.get("status", "pending"),
                    createdAt=r["createdAt"],
                    reporterUserId=r.get("reporterUserId", ""),
                    reporterUsername=reporter_username,
                    targetExists=target_exists,
                    targetUsername=target_username,
                    targetDisplayName=target_display_name,
                    targetContent=target_content,
                    targetImageCount=target_image_count,
                    targetProfilePicture=target_picture,
                )
            )
        return items

    async def get_reports_admin(
        self,
        limit: int = 20,
        cursor: Optional[str] = None,
        target_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> AdminReportPaginationResponse:
        cursor_dict = None
        if cursor:
            try:
                parts = cursor.split("_")
                cursor_dict = {
                    "createdAt": datetime.fromisoformat(parts[0]),
                    "reportId": parts[1],
                }
            except Exception:
                pass

        reports = await self.repository.get_reports(
            limit + 1, cursor_dict, target_type, status
        )

        has_more = len(reports) > limit
        if has_more:
            reports = reports[:limit]

        items = await self._enrich_reports(reports)
        total = await self.repository.count_reports(target_type, status)

        next_cursor = None
        if has_more and reports:
            last = reports[-1]
            next_cursor = f"{last['createdAt'].isoformat()}_{last['reportId']}"

        return AdminReportPaginationResponse(
            data=items,
            meta=AdminReportPaginationMeta(
                nextCursor=next_cursor, hasMore=has_more, total=total
            ),
        )

    async def delete_post(self, post_id: str, user_id: str, is_admin: bool = False):
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()

        if not is_admin and post["userId"] != user_id:
            raise UnauthorizedActionError()

        await self.repository.delete_post(post_id)
        await self.repository.delete_poll_votes(post_id)

        if post.get("parentPostId"):
            await self.repository.increment_post_stats(
                post["parentPostId"], "replyCount", -1
            )

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
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more),
        )

    async def get_user_replies(
        self,
        target_username: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        current_user_id: Optional[str] = None,
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

        posts = await self.repository.get_user_replies(
            target_username, limit + 1, cursor_dict
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
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more),
        )

    async def get_user_bookmarks(
        self, user_id: str, limit: int = 20, cursor: Optional[str] = None
    ) -> PostPaginationResponse:
        cursor_dict = None
        if cursor:
            try:
                parts = cursor.split("_")
                cursor_dict = {
                    "createdAt": datetime.fromisoformat(parts[0]),
                    "_id": parts[1],  # Need ObjectId for bookmark pagination
                }
            except Exception:
                pass

        result = await self.repository.get_user_bookmarks(
            user_id, limit + 1, cursor_dict
        )
        bookmarks = result["bookmarks"]
        posts_by_id = {p["postId"]: p for p in result["posts"]}

        has_more = len(bookmarks) > limit
        if has_more:
            bookmarks = bookmarks[:limit]

        ordered_posts = [
            posts_by_id[b["postId"]] for b in bookmarks if b["postId"] in posts_by_id
        ]
        enriched_posts = await self._enrich_posts(ordered_posts, user_id)

        next_cursor = None
        if has_more and bookmarks:
            last_b = bookmarks[-1]
            next_cursor = f"{last_b['createdAt'].isoformat()}_{str(last_b['_id'])}"

        return PostPaginationResponse(
            data=enriched_posts,
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more),
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
        repost_count = await self.repository.count_user_reposts(user.get("userId", ""))

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
