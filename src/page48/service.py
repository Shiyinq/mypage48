import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Union

from pymongo.errors import DuplicateKeyError

from src.auth.schemas import UserCurrent
from src.config import Settings
from src.infrastructure import AsyncBackgroundRunner
from src.logging_config import create_logger
from src.page48.exceptions import (
    CannotBlockSelfError,
    CannotFollowSelfError,
    CannotMuteSelfError,
    CannotPinReplyError,
    CannotPrivateReplyError,
    CannotReportSelfError,
    InvalidImageError,
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
    QuotedPostNotFoundError,
    QuotePollConflictError,
    ReportAlreadyExistsError,
    ReportCreationError,
    ThreadTooLongError,
    ThreadTooShortError,
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
    BlockResponse,
    CreatePostRequest,
    CreateThreadRequest,
    CreateThreadResponse,
    EditPostRequest,
    FollowResponse,
    MarkNotificationsReadResponse,
    MuteResponse,
    NotificationCountsResponse,
    NotificationItem,
    NotificationOverviewResponse,
    NotificationPaginationMeta,
    NotificationPaginationResponse,
    NotificationPostPreview,
    NotificationTabSummary,
    Page48Image,
    Page48SettingsResponse,
    Page48UserProfileResponse,
    Page48Video,
    PollOptionResponse,
    PollResponse,
    PostActivityResponse,
    PostPaginationMeta,
    PostPaginationResponse,
    PostResponse,
    PostUserItem,
    PostUserListMeta,
    PostUserListResponse,
    ReportCreate,
    ReportResponse,
    SearchTopResponse,
    ThreadPostItem,
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
# Mentions are matched the same informal way as hashtags: a run of username
# characters right after an `@`.
MENTION_PATTERN = re.compile(r"(?:^|[^\w@])@(\w{1,50})", re.UNICODE)
MAX_MENTIONS = 10
NOTIFICATION_LIMIT_DEFAULT = 20
# How many notifications the overview shows per tab as a preview.
NOTIFICATION_OVERVIEW_PREVIEW = 2
# Protects a recipient from a viral post: only the newest ones are kept.
NOTIFICATION_MAX_PER_USER = 500
# These can be repeated by the same actor, so they carry a dedupe key.
NOTIFICATION_DEDUPED_TYPES = {"like", "repost", "follow", "followRequest"}
# Search. Free words match token prefixes, so the collection is never scanned.
SEARCH_TOKEN_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)
SEARCH_TOKEN_MIN_LENGTH = 2
MAX_SEARCH_TOKENS = 60
MAX_SEARCH_WORDS = 5
SEARCH_QUERY_MIN_LENGTH = 2
SEARCH_LIMIT_DEFAULT = 20
SEARCH_USERS_LIMIT = 20
SEARCH_TAGS_LIMIT = 30
SEARCH_TOP_USERS = 3
SEARCH_TOP_TAGS = 3
SEARCH_TOP_POSTS = 10
# Which notification types each tab shows. Quotes ride along with reposts,
# exactly like the repost icon counts them.
NOTIFICATION_TABS = {
    "replies": ["reply"],
    "mentions": ["mention"],
    "follows": ["follow", "followRequest", "followAccepted"],
    "likes": ["like"],
    "reposts": ["repost", "quote"],
    "all": [
        "reply",
        "mention",
        "follow",
        "followRequest",
        "followAccepted",
        "like",
        "repost",
        "quote",
    ],
}
# A tab and its badge counts. The tabs shown in the UI, in order.
NOTIFICATION_TAB_KEYS = ["replies", "mentions", "likes", "reposts", "follows"]
# Every type belongs to exactly one tab, so a count can be filed without guessing.
NOTIFICATION_TYPE_TAB = {
    "reply": "replies",
    "mention": "mentions",
    "follow": "follows",
    "followRequest": "follows",
    "followAccepted": "follows",
    "like": "likes",
    "repost": "reposts",
    "quote": "reposts",
}
POLL_DURATION_HOURS = 24
MIN_POLL_OPTIONS = 2
MAX_POLL_OPTIONS = 6
MAX_POLL_OPTION_LENGTH = 50
MIN_THREAD_POSTS = 2
MAX_THREAD_POSTS = 25
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
        # Authors excluded from every post read this request; computed lazily.
        self._hidden_authors: Optional[List[str]] = None

    async def _hidden_author_ids(self, viewer_id: Optional[str]) -> List[str]:
        """Authors whose posts this viewer must not read.

        Blocks (either direction) and locked accounts the viewer does not follow
        land here. It is computed once per request and reused by every query, so
        the rule cannot be forgotten in one place and applied in another.
        """
        if self._hidden_authors is None:
            hidden: set = set()
            if viewer_id:
                hidden |= set(await self.repository.get_blocked_ids(viewer_id))
            # A locked account is follower-only: guests and non-followers are
            # outside. The flag lives apart from the MyPage48 stats flag.
            locked = set(await self.user_repository.get_page48_locked_ids())
            if locked:
                following = (
                    set(await self.repository.get_following_ids(viewer_id))
                    if viewer_id
                    else set()
                )
                hidden |= locked - following
            hidden.discard(viewer_id or "")
            self._hidden_authors = list(hidden)
        return self._hidden_authors

    async def _author_hidden_for(
        self, viewer_id: Optional[str], author_id: Optional[str]
    ) -> bool:
        """Whether one author's posts are off-limits to one viewer.

        Unlike `_hidden_author_ids` this is neither cached nor tied to the
        request's viewer, so it can guard a notification aimed at somebody else.
        """
        if not author_id or author_id == viewer_id:
            return False
        if viewer_id:
            blocked = set(await self.repository.get_blocked_ids(viewer_id))
            if author_id in blocked:
                return True
        author = await self.user_repository.find_one({"userId": author_id})
        if not author or not author.get("page48Locked"):
            return False
        if not viewer_id:
            return True
        following = set(await self.repository.get_following_ids(viewer_id))
        return author_id not in following

    async def _visibility(self, viewer_id: Optional[str]) -> Optional[dict]:
        """Mongo condition for the posts a viewer may not see.

        Two rules apply everywhere posts are read: authors hidden from the viewer
        (blocks / locked accounts) are dropped, and a private post is dropped
        unless the viewer wrote it.
        """
        hidden = await self._hidden_author_ids(viewer_id)
        conditions: List[dict] = []
        if hidden:
            conditions.append({"userId": {"$nin": hidden}})
        if viewer_id:
            conditions.append(
                {"$or": [{"isPrivate": {"$ne": True}}, {"userId": viewer_id}]}
            )
        else:
            conditions.append({"isPrivate": {"$ne": True}})

        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    async def _assert_post_visible(
        self, post: dict, viewer_id: Optional[str]
    ) -> None:
        """A direct link has to respect visibility: hidden posts look missing."""
        hidden = await self._hidden_author_ids(viewer_id)
        if post.get("userId") in hidden:
            raise PostNotFoundError()
        # A private post is nobody else's to open, not even via its link.
        if post.get("isPrivate") and post.get("userId") != viewer_id:
            raise PostNotFoundError()

    async def _muted_author_ids(self, viewer_id: Optional[str]) -> List[str]:
        """Muted accounts: hidden from the timeline only, never from search."""
        if not viewer_id:
            return []
        return await self.repository.get_muted_ids(viewer_id)

    async def _resolve_author_avatar(
        self, post: dict, user_map: Optional[dict], cache: dict
    ) -> tuple[Optional[str], Optional[str]]:
        """Resolve the author's *current* avatar (by userId), cached per request.

        The avatar is always read from the live user document: posts only store
        the author's `userId`, never a copy of the picture path.
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
        thread_count: int = 0,
        quote_count: int = 0,
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

        # Identity is read exclusively from the live user document: posts only
        # carry the immutable `userId`, so a rename or a new picture is
        # reflected everywhere at once.
        author = (user_map or {}).get(post.get("userId")) or {}
        username = author.get("username") or ""
        display_name = author.get("name") or username
        blur_hash = author.get("blurHash")

        return PostResponse(
            postId=post["postId"],
            rootPostId=post.get("rootPostId"),
            parentPostId=post.get("parentPostId"),
            depth=post.get("depth", 0),
            replyCount=post.get("replyCount", 0),
            userId=post["userId"],
            username=username,
            userDisplayName=display_name,
            userProfilePicture=user_picture,
            userProfilePicture_small=user_picture_small,
            userBlurHash=blur_hash,
            content=post["content"],
            images=images,
            videos=videos,
            tags=post.get("tags", []),
            likesCount=post.get("likesCount", 0),
            repostCount=post.get("repostCount", 0),
            quoteCount=quote_count,
            bookmarksCount=post.get("bookmarksCount", 0),
            isEdited=post.get("isEdited", False),
            createdAt=post["createdAt"],
            updatedAt=post["updatedAt"],
            isPinned=bool(post.get("pinnedAt")),
            isPrivate=bool(post.get("isPrivate")),
            isLiked=interactions.get("isLiked", False),
            isReposted=interactions.get("isReposted", False),
            isBookmarked=interactions.get("isBookmarked", False),
            threadCount=thread_count,
            quotedPostId=post.get("quotedPostId"),
            poll=(
                self._build_poll_response(
                    post["poll"], poll_counts, interactions.get("pollOptionId")
                )
                if post.get("poll")
                else None
            ),
        )

    async def _enrich_posts(
        self,
        posts: List[dict],
        user_id: Optional[str] = None,
        include_quotes: bool = True,
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

        thread_counts = await self._count_self_threads(posts)
        # Live, like the activity tabs: quotes are never denormalized on the post.
        quote_counts = await self.repository.count_quotes_for_posts(post_ids)

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
                    thread_counts.get(p["postId"], 0),
                    quote_counts.get(p["postId"], 0),
                )
            )

        if include_quotes:
            await self._attach_quoted_posts(posts, enriched, user_id)

        return enriched

    async def _attach_quoted_posts(
        self,
        posts: List[dict],
        enriched: List[PostResponse],
        user_id: Optional[str],
    ) -> None:
        """Fill in each post's `quotedPost` preview, one level deep only."""
        by_id = {item.postId: item for item in enriched}
        quoted_ids = [
            post["quotedPostId"] for post in posts if post.get("quotedPostId")
        ]
        # A quoted post may be part of this same batch; only fetch the rest.
        missing = [qid for qid in dict.fromkeys(quoted_ids) if qid not in by_id]
        visibility = await self._visibility(user_id)
        if missing:
            rows = await self.repository.get_posts_by_ids(missing, visibility)
            nested = await self._enrich_posts(rows, user_id, include_quotes=False)
            for quoted in nested:
                by_id[quoted.postId] = quoted

        for post, enriched_post in zip(posts, enriched):
            quoted_id = post.get("quotedPostId")
            if quoted_id and quoted_id != enriched_post.postId:
                # A dangling id (the original was deleted) stays None, which the
                # client renders as an "unavailable" placeholder.
                quoted = by_id.get(quoted_id)
                if quoted is not None and quoted.quotedPost is not None:
                    # The preview itself was a quote (it came from this same
                    # batch); never embed more than one level deep.
                    quoted = quoted.model_copy(update={"quotedPost": None})
                enriched_post.quotedPost = quoted

    async def _count_self_threads(self, posts: List[dict]) -> dict:
        """Thread size starting at each post, the post itself included.

        A thread is a linear chain of posts by one author, so one extra query per
        page is enough; the chain is then walked in memory. Posts that nothing
        continues are left out of the result (they are not a thread).
        """
        root_ids = [p["postId"] for p in posts if not p.get("parentPostId")]
        if not root_ids:
            return {}

        descendants = await self.repository.get_posts_by_root_ids(root_ids)
        children: dict = {}
        for post in descendants:
            children.setdefault(post.get("parentPostId"), []).append(post)

        counts = {}
        for start in posts:
            count = 1
            current = start
            # Bounded so a broken chain can never loop forever.
            for _ in range(MAX_THREAD_POSTS):
                continuations = [
                    child
                    for child in children.get(current["postId"], [])
                    if child.get("userId") == start.get("userId")
                ]
                if not continuations:
                    break

                continuations.sort(key=lambda child: child.get("createdAt"))
                current = continuations[0]
                count += 1

            if count > 1:
                counts[start["postId"]] = count

        return counts

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
        # Documents come back from Mongo with naive datetimes (the driver is not
        # tz-aware), so the stored value has to be read as UTC before comparing.
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)
        return (now or datetime.now(timezone.utc)) >= ends_at

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

    def _extract_mentions(self, content: str) -> List[str]:
        """Usernames mentioned with `@` in the content, lower-cased and deduped."""
        mentions: List[str] = []
        for match in MENTION_PATTERN.findall(content or ""):
            username = match.lower()
            if username and username not in mentions:
                mentions.append(username)
        return mentions[:MAX_MENTIONS]

    def _extract_search_tokens(self, content: str) -> List[str]:
        """Lower-cased words of the content, deduped and capped for post search."""
        tokens: List[str] = []
        for match in SEARCH_TOKEN_PATTERN.findall(content or ""):
            token = match.lower()
            if len(token) < SEARCH_TOKEN_MIN_LENGTH or token in tokens:
                continue
            tokens.append(token)
            if len(tokens) >= MAX_SEARCH_TOKENS:
                break
        return tokens

    def _parse_search_query(self, query: str) -> dict:
        """Split a raw query into free words plus `from:`/`#`/`@` operators."""
        words: List[str] = []
        tags: List[str] = []
        mentions: List[str] = []
        authors: List[str] = []

        for part in (query or "").split():
            lowered = part.lower()
            if lowered.startswith("from:") and len(lowered) > len("from:"):
                authors.append(lowered[len("from:") :])
            elif lowered.startswith("#") and len(lowered) > 1:
                tags.append(lowered[1:])
            elif lowered.startswith("@") and len(lowered) > 1:
                mentions.append(lowered[1:])
            elif len(lowered) >= SEARCH_TOKEN_MIN_LENGTH:
                words.append(lowered)

        return {
            "words": words[:MAX_SEARCH_WORDS],
            "tags": tags,
            "mentions": mentions,
            "authors": authors,
        }

    @staticmethod
    def _has_search_criteria(parsed: dict) -> bool:
        return bool(
            parsed["words"]
            or parsed["tags"]
            or parsed["mentions"]
            or parsed["authors"]
        )

    def _search_term_for_people(self, query: str) -> str:
        """Text a people/tag tab searches: the free words, else the operator value."""
        parsed = self._parse_search_query(query)
        if parsed["words"]:
            return " ".join(parsed["words"])
        for key in ("authors", "mentions", "tags"):
            if parsed[key]:
                return parsed[key][0]
        return ""

    @staticmethod
    def _rank_search_users(users: List[dict], term: str) -> List[dict]:
        """Exact username first, then username prefix, then the rest."""
        lowered = (term or "").lower()

        def rank(user: dict) -> int:
            username = (user.get("username") or "").lower()
            if lowered and username == lowered:
                return 0
            if lowered and username.startswith(lowered):
                return 1
            return 2

        return sorted(users, key=rank)

    async def _notify(
        self,
        recipient_user_id: Optional[str],
        actor_user_id: str,
        notification_type: str,
        post_id: Optional[str] = None,
    ) -> None:
        """Record one notification.

        Nobody is notified about their own action, and a notification failure
        must never break the action that triggered it, so errors are only logged.
        """
        if not recipient_user_id or recipient_user_id == actor_user_id:
            return

        # Like, repost and follow can be repeated by the same actor, so they carry
        # a key the sparse unique index uses to keep a single row.
        dedupe_key = None
        if notification_type in NOTIFICATION_DEDUPED_TYPES:
            dedupe_key = (
                f"{recipient_user_id}:{notification_type}:{post_id or ''}:"
                f"{actor_user_id}"
            )

        try:
            await self.repository.upsert_notification(
                {
                    "notificationId": str(uuid.uuid4()),
                    "recipientUserId": recipient_user_id,
                    "actorUserId": actor_user_id,
                    "type": notification_type,
                    "postId": post_id,
                    "readAt": None,
                    "createdAt": datetime.now(timezone.utc),
                },
                dedupe_key,
            )
            # Only the noisy types can pile up, so only they pay for the cap check.
            if notification_type in NOTIFICATION_DEDUPED_TYPES:
                await self.repository.prune_notifications(
                    recipient_user_id, NOTIFICATION_MAX_PER_USER
                )
        except DuplicateKeyError:
            # A concurrent action won the upsert; one row is all we want.
            pass
        except Exception as error:
            logger.error(f"Failed to record notification: {str(error)}")

    async def _queue_post_notifications(
        self, post_data: dict, actor_user_id: str
    ) -> None:
        """Fan out a new post's notifications off the request path.

        Looking up the mentioned users, the parent post and the quoted post would
        otherwise all happen inside `POST /posts`.
        """
        if self.background_tasks:
            self.background_tasks.add_task(
                self._notify_post_created, post_data, actor_user_id
            )
        else:
            await self._notify_post_created(post_data, actor_user_id)

    async def _notify_post_created(self, post_data: dict, actor_user_id: str) -> None:
        """Mention, reply and quote notifications for a freshly created post.

        A mention wins over a reply for the same recipient: a reply that names
        the author is filed under mentions only, never under both.
        """
        post_id = post_data["postId"]
        notified: set = set()

        async def can_reach(recipient_id: Optional[str]) -> bool:
            """Only notify someone who is allowed to see the new post."""
            if not recipient_id:
                return False
            return not await self._author_hidden_for(recipient_id, actor_user_id)

        usernames = self._extract_mentions(post_data.get("content", ""))
        if usernames:
            users = await self.user_repository.get_users_by_usernames(usernames)
            for mentioned in users:
                mentioned_id = mentioned.get("userId")
                if not mentioned_id or mentioned_id in notified:
                    continue
                if not await can_reach(mentioned_id):
                    continue
                notified.add(mentioned_id)
                await self._notify(mentioned_id, actor_user_id, "mention", post_id)

        parent_id = post_data.get("parentPostId")
        if parent_id:
            parent = await self.repository.get_post_by_id(parent_id)
            parent_author = parent.get("userId") if parent else None
            if parent_author and parent_author not in notified:
                if await can_reach(parent_author):
                    notified.add(parent_author)
                    await self._notify(parent_author, actor_user_id, "reply", post_id)

        quoted_id = post_data.get("quotedPostId")
        if quoted_id:
            quoted = await self.repository.get_post_by_id(quoted_id)
            quoted_author = quoted.get("userId") if quoted else None
            if quoted_author and quoted_author not in notified:
                if await can_reach(quoted_author):
                    notified.add(quoted_author)
                    await self._notify(quoted_author, actor_user_id, "quote", post_id)

    async def get_trending_tags(
        self, limit: int = 10, viewer_id: Optional[str] = None
    ) -> TrendingTagsResponse:
        rows = await self.repository.get_trending_tags(
            limit, await self._visibility(viewer_id)
        )
        return TrendingTagsResponse(
            tags=[TrendingTag(tag=row["_id"], count=row["count"]) for row in rows]
        )

    # Search
    async def search_posts(
        self,
        query: str,
        current_user_id: str,
        tab: str = "posts",
        limit: int = SEARCH_LIMIT_DEFAULT,
        cursor: Optional[str] = None,
    ) -> PostPaginationResponse:
        empty = PostPaginationResponse(
            data=[], meta=PostPaginationMeta(nextCursor=None, hasMore=False)
        )
        if len((query or "").strip()) < SEARCH_QUERY_MIN_LENGTH:
            return empty

        parsed = self._parse_search_query(query)
        if not self._has_search_criteria(parsed):
            return empty

        author_ids = await self._resolve_search_authors(parsed["authors"])
        if author_ids is None:
            # `from:` named an account that does not exist, so nothing can match.
            return empty

        rows = await self.repository.search_posts(
            {
                "words": parsed["words"],
                "tags": parsed["tags"],
                "mentions": parsed["mentions"],
                "author_ids": author_ids,
                "media": "media" if tab == "media" else None,
            },
            limit + 1,
            self._parse_post_cursor(cursor),
            await self._visibility(current_user_id),
        )

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        next_cursor = None
        if has_more and rows:
            last = rows[-1]
            next_cursor = f"{last['createdAt'].isoformat()}_{last['postId']}"

        return PostPaginationResponse(
            data=await self._enrich_posts(rows, current_user_id),
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more),
        )

    async def search_users(
        self, query: str, current_user_id: str, limit: int = SEARCH_USERS_LIMIT
    ) -> PostUserListResponse:
        term = self._search_term_for_people(query)
        empty = PostUserListResponse(
            data=[], meta=PostUserListMeta(nextCursor=None, hasMore=False)
        )
        if len(term.strip()) < SEARCH_QUERY_MIN_LENGTH:
            return empty

        users = await self.user_repository.search_users(term, limit)
        return PostUserListResponse(
            data=await self._build_search_users(
                self._rank_search_users(users, term), current_user_id
            ),
            meta=PostUserListMeta(nextCursor=None, hasMore=False),
        )

    async def search_tags(
        self,
        query: str,
        limit: int = SEARCH_TAGS_LIMIT,
        viewer_id: Optional[str] = None,
    ) -> TrendingTagsResponse:
        term = self._search_term_for_people(query)
        rows = await self.repository.search_tags(
            term, limit, await self._visibility(viewer_id)
        )
        return TrendingTagsResponse(
            tags=[TrendingTag(tag=row["_id"], count=row["count"]) for row in rows]
        )

    async def search_top(self, query: str, current_user_id: str) -> SearchTopResponse:
        """Overview tab: a few people, a few tags, then the newest posts."""
        users = await self.search_users(query, current_user_id, SEARCH_TOP_USERS)
        tags = await self.search_tags(query, SEARCH_TOP_TAGS, current_user_id)
        posts = await self.search_posts(
            query, current_user_id, "posts", SEARCH_TOP_POSTS
        )
        return SearchTopResponse(users=users.data, tags=tags.tags, posts=posts.data)

    async def _resolve_search_authors(
        self, usernames: List[str]
    ) -> Optional[List[str]]:
        """Map `from:` usernames to ids; None means one of them does not exist."""
        if not usernames:
            return []
        users = await self.user_repository.get_users_by_usernames(usernames)
        found = {(user.get("username") or "").lower() for user in users}
        if any(name not in found for name in usernames):
            return None
        return list({user["userId"] for user in users if user.get("userId")})

    async def _build_search_users(
        self, users: List[dict], viewer_id: Optional[str]
    ) -> List[PostUserItem]:
        if not users:
            return []

        hidden = await self._hidden_author_ids(viewer_id)
        if hidden:
            users = [user for user in users if user.get("userId") not in hidden]
            if not users:
                return []

        followed: set = set()
        pending: set = set()
        if viewer_id:
            user_ids = [user["userId"] for user in users]
            followed = set(
                await self.repository.get_followed_ids(viewer_id, user_ids)
            )
            pending = set(
                await self.repository.get_pending_follow_ids(viewer_id, user_ids)
            )

        picture_cache: dict = {}
        items: List[PostUserItem] = []
        for user in users:
            picture, picture_small = await self._resolve_picture_variants(
                user.get("profilePicture"), picture_cache
            )
            items.append(
                PostUserItem(
                    userId=user.get("userId", ""),
                    username=user.get("username") or "",
                    name=user.get("name") or user.get("username") or "",
                    profilePicture=picture,
                    profilePicture_small=picture_small,
                    bio=user.get("bio"),
                    isFollowing=user.get("userId") in followed,
                    isPending=user.get("userId") in pending,
                )
            )
        return items

    async def get_active_users(
        self,
        limit: int = 5,
        days: int = 7,
        exclude_user_id: Optional[str] = None,
    ) -> ActiveUsersResponse:
        """Most active (most top-level posts) users in the last `days`."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        # Fetch one extra row when we may need to drop the current user.
        rows = await self.repository.get_most_active_users(
            limit + 1 if exclude_user_id else limit,
            since,
            # The same id doubles as the viewer, so locked or blocked accounts
            # never surface in this public list.
            await self._visibility(exclude_user_id),
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
                    username=(user or {}).get("username") or "",
                    name=(user or {}).get("name") or "",
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
            normalized,
            limit + 1,
            cursor_dict,
            media,
            await self._visibility(user_id),
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

    async def _build_post_document(
        self,
        data: Union[CreatePostRequest, ThreadPostItem],
        user: UserCurrent,
        parent_post_id: Optional[str] = None,
        now: Optional[datetime] = None,
        post_id: Optional[str] = None,
    ) -> dict:
        """Validate one draft and build its post document (no insert).

        Shared by `create_post` and `create_thread` so both paths enforce exactly
        the same rules. `parent_post_id` is passed in rather than read from the
        draft, because a thread chains onto posts created in the same request.
        """
        post_id = post_id or str(uuid.uuid4())
        now = now or datetime.now(timezone.utc)

        root_post_id = None
        depth = 0
        # A reply inherits its parent's privacy, so continuing a private thread
        # (or replying under a private post) never leaks the new post.
        is_private = False

        if parent_post_id:
            parent = await self.repository.get_post_by_id(parent_post_id)
            if not parent:
                raise PostNotFoundError()
            # A reply must not expose, or chain onto, a post its author is not
            # allowed to read.
            await self._assert_post_visible(parent, user.userId)

            root_post_id = parent.get("rootPostId") or parent_post_id
            depth = parent.get("depth", 0) + 1
            is_private = bool(parent.get("isPrivate"))

            # Update reply count of parent
            await self.repository.increment_post_stats(parent_post_id, "replyCount", 1)

        # Every image must live under the uploader's own prefix, exactly like a
        # video: the read side signs whatever path a post carries, so an
        # unvalidated reference would turn a public post into a signed-URL
        # oracle for arbitrary stored objects (other users' files, other
        # services) and let external/data: URLs into the feed.
        image_prefix = f"page48/{user.userId}/"
        images_data = []
        for ref in data.images:
            filename = (ref.filename or "").strip()
            if not filename.startswith(image_prefix) or ".." in filename:
                raise InvalidImageError()
            images_data.append(
                {
                    "filename": filename,
                    "width": ref.width or 0,
                    "height": ref.height or 0,
                }
            )
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

        # A quote is an ordinary post that embeds a preview of another one.
        quoted_post_id = getattr(data, "quotedPostId", None)
        if quoted_post_id:
            quoted_post = await self.repository.get_post_by_id(quoted_post_id)
            if not quoted_post:
                raise QuotedPostNotFoundError()
            # You can only quote a post you are allowed to read.
            await self._assert_post_visible(quoted_post, user.userId)

        poll_data = None
        if data.poll is not None:
            if images_data or videos_data:
                raise PollMediaConflictError()
            if quoted_post_id:
                raise QuotePollConflictError()
            if parent_post_id:
                raise PollReplyNotAllowedError()
            poll_data = {
                "endsAt": now + timedelta(hours=POLL_DURATION_HOURS),
                "options": self._build_poll_options(data.poll.options),
            }

        return {
            "postId": post_id,
            "rootPostId": root_post_id,
            "parentPostId": parent_post_id,
            "depth": depth,
            "replyCount": 0,
            "userId": user.userId,
            "content": data.content,
            "images": images_data,
            "videos": videos_data,
            "poll": poll_data,
            "tags": tags,
            "searchTokens": self._extract_search_tokens(data.content),
            "mentions": self._extract_mentions(data.content),
            "quotedPostId": quoted_post_id,
            "pinnedAt": None,
            "isPrivate": is_private,
            "likesCount": 0,
            "repostCount": 0,
            "bookmarksCount": 0,
            "isEdited": False,
            "createdAt": now,
            "updatedAt": now,
        }

    async def create_post(
        self, data: CreatePostRequest, user: UserCurrent
    ) -> PostResponse:
        try:
            post_data = await self._build_post_document(
                data, user, parent_post_id=data.parentPostId
            )
            await self.repository.insert_post(post_data)
            await self._queue_post_notifications(post_data, user.userId)

            # Enrich and return (via the batch helper so a quote preview is
            # attached exactly like it is everywhere else).
            posts = await self._enrich_posts([post_data], user.userId)
            return posts[0]

        except (
            PostNotFoundError,
            QuotedPostNotFoundError,
            MediaConflictError,
            MaxVideoExceededError,
            InvalidVideoError,
            InvalidImageError,
            InvalidPollOptionsError,
            PollMediaConflictError,
            QuotePollConflictError,
            PollReplyNotAllowedError,
        ):
            raise
        except Exception as e:
            logger.exception(f"Error creating post: {str(e)}")
            raise PostCreationError()

    async def create_thread(
        self, data: CreateThreadRequest, user: UserCurrent
    ) -> CreateThreadResponse:
        """Publish a chain of posts, each one replying to the previous."""
        try:
            count = len(data.posts)
            if count < MIN_THREAD_POSTS:
                raise ThreadTooShortError()
            if count > MAX_THREAD_POSTS:
                raise ThreadTooLongError()

            now = datetime.now(timezone.utc)
            documents: List[dict] = []
            parent_post_id: Optional[str] = None

            for item in data.posts:
                post_data = await self._build_post_document(
                    item, user, parent_post_id=parent_post_id, now=now
                )
                # Insert as we go, so the next post can chain onto this one.
                await self.repository.insert_post(post_data)
                await self._queue_post_notifications(post_data, user.userId)
                documents.append(post_data)
                parent_post_id = post_data["postId"]

            posts = await self._enrich_posts(documents, user.userId)
            return CreateThreadResponse(rootPostId=documents[0]["postId"], posts=posts)

        except (
            ThreadTooShortError,
            ThreadTooLongError,
            PostNotFoundError,
            QuotedPostNotFoundError,
            MediaConflictError,
            MaxVideoExceededError,
            InvalidVideoError,
            InvalidImageError,
            InvalidPollOptionsError,
            PollMediaConflictError,
            QuotePollConflictError,
            PollReplyNotAllowedError,
        ):
            raise
        except Exception as e:
            logger.exception(f"Error creating thread: {str(e)}")
            raise PostCreationError()

    async def get_feed(
        self,
        limit: int = 20,
        cursor: Optional[str] = None,
        user_id: Optional[str] = None,
        media: Optional[str] = None,
        following: bool = False,
    ) -> PostPaginationResponse:
        cursor_dict = self._parse_post_cursor(cursor)

        author_ids = None
        if following:
            if not user_id:
                raise UnauthorizedActionError()
            author_ids = await self.repository.get_following_ids(user_id)
            if not author_ids:
                # Following nobody yet: an empty page, not an error.
                return PostPaginationResponse(
                    data=[], meta=PostPaginationMeta(nextCursor=None, hasMore=False)
                )

        posts = await self.repository.get_feed(
            limit + 1,
            cursor_dict,
            media,
            author_ids,
            await self._visibility(user_id),
            await self._muted_author_ids(user_id),
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

    async def get_post(
        self, post_id: str, user_id: Optional[str] = None
    ) -> PostResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()

        await self._assert_post_visible(post, user_id)

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

        await self._assert_post_visible(post, user_id)

        root_id = post.get("rootPostId") or post_id

        # Get all posts in this thread (root + all replies)
        if root_id == post_id:
            all_raw = [post]
        else:
            root_post = await self.repository.get_post_by_id(root_id)
            all_raw = [root_post] if root_post else []

        replies_raw = await self.repository.get_thread_replies(
            root_id, await self._visibility(user_id)
        )

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
            post_id,
            limit + 1,
            cursor_dict,
            await self._visibility(user_id),
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

    # Post activity (quotes / reposts / likes)
    @staticmethod
    def _parse_post_cursor(cursor: Optional[str]) -> Optional[dict]:
        if not cursor:
            return None
        try:
            created_at, post_id = cursor.split("_")
            return {"createdAt": datetime.fromisoformat(created_at), "postId": post_id}
        except Exception:
            return None

    @staticmethod
    def _parse_interaction_cursor(cursor: Optional[str]) -> Optional[dict]:
        if not cursor:
            return None
        try:
            created_at, doc_id = cursor.split("_")
            return {"createdAt": datetime.fromisoformat(created_at), "_id": doc_id}
        except Exception:
            return None

    async def get_post_activity(
        self, post_id: str, current_user_id: Optional[str] = None
    ) -> PostActivityResponse:
        """Counts and context for the post's activity page."""
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()

        await self._assert_post_visible(post, current_user_id)

        # Counted live so a tab label can never disagree with its own list, using
        # the same visibility rule the lists themselves apply.
        visibility = await self._visibility(current_user_id)
        quote_count = await self.repository.count_post_quotes(post_id, visibility)
        repost_count = await self.repository.count_post_reposts(post_id, visibility)
        like_count = await self.repository.count_post_likes(post_id, visibility)

        enriched = (await self._enrich_posts([post], current_user_id))[0]
        return PostActivityResponse(
            post=enriched,
            quoteCount=quote_count,
            repostCount=repost_count,
            likeCount=like_count,
            canViewLikes=(
                bool(current_user_id) and post.get("userId") == current_user_id
            ),
        )

    # Notifications
    async def get_notifications(
        self,
        current_user_id: str,
        tab: str = "all",
        limit: int = NOTIFICATION_LIMIT_DEFAULT,
        cursor: Optional[str] = None,
    ) -> NotificationPaginationResponse:
        types = None if tab == "all" else NOTIFICATION_TABS.get(tab)
        rows = await self.repository.get_notifications(
            current_user_id, limit + 1, self._parse_notification_cursor(cursor), types
        )

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        next_cursor = None
        if has_more and rows:
            last = rows[-1]
            next_cursor = f"{last['createdAt'].isoformat()}_{last['notificationId']}"

        return NotificationPaginationResponse(
            data=await self._build_notifications(rows, current_user_id),
            meta=NotificationPaginationMeta(
                nextCursor=next_cursor, hasMore=has_more
            ),
        )

    async def get_notification_counts(
        self, current_user_id: str
    ) -> NotificationCountsResponse:
        by_type = await self.repository.count_unread_notifications_by_type(
            current_user_id, await self._hidden_author_ids(current_user_id)
        )
        counts = {tab: 0 for tab in NOTIFICATION_TAB_KEYS}
        for type_name, count in by_type.items():
            tab = NOTIFICATION_TYPE_TAB.get(type_name)
            if tab:
                counts[tab] += count
        return NotificationCountsResponse(total=sum(counts.values()), **counts)

    async def get_notification_overview(
        self, current_user_id: str
    ) -> NotificationOverviewResponse:
        """Counts plus the latest few notifications of every tab.

        Each tab contributes at most `NOTIFICATION_OVERVIEW_PREVIEW` rows and all
        of them are enriched in one batch, so the actors still cost a single query.
        """
        counts = await self.get_notification_counts(current_user_id)

        rows: List[dict] = []
        for tab in NOTIFICATION_TAB_KEYS:
            rows.extend(
                await self.repository.get_notifications(
                    current_user_id,
                    NOTIFICATION_OVERVIEW_PREVIEW,
                    None,
                    NOTIFICATION_TABS[tab],
                )
            )

        items = await self._build_notifications(rows, current_user_id)
        by_id = {item.notificationId: item for item in items}

        tabs: List[NotificationTabSummary] = []
        for tab in NOTIFICATION_TAB_KEYS:
            previews = [
                by_id[row["notificationId"]]
                for row in rows
                if row["notificationId"] in by_id
                and NOTIFICATION_TYPE_TAB.get(row["type"]) == tab
            ]
            tabs.append(
                NotificationTabSummary(
                    tab=tab, count=getattr(counts, tab), previews=previews
                )
            )

        return NotificationOverviewResponse(total=counts.total, tabs=tabs)

    async def mark_notifications_read(
        self, current_user_id: str, tab: str = "all"
    ) -> MarkNotificationsReadResponse:
        """Mark one tab (or everything) read; the badge follows the counts."""
        types = NOTIFICATION_TABS.get(tab) or NOTIFICATION_TABS["all"]
        count = await self.repository.mark_notifications_read(
            current_user_id, types, datetime.now(timezone.utc)
        )
        return MarkNotificationsReadResponse(count=count)

    async def _build_notifications(
        self, rows: List[dict], viewer_id: Optional[str]
    ) -> List[NotificationItem]:
        """Resolve the actors and post snippets of a page of notifications."""
        if not rows:
            return []

        # A blocked or hidden actor's notification is dropped entirely, and their
        # post snippets never resolve, so nothing leaks through the list.
        hidden = await self._hidden_author_ids(viewer_id)
        if hidden:
            rows = [row for row in rows if row.get("actorUserId") not in hidden]
            if not rows:
                return []

        # Actors come from the user documents; post snippets use a narrow
        # projection, so no media URL is ever signed for a text preview.
        post_ids = list({row["postId"] for row in rows if row.get("postId")})
        posts = await self.repository.get_notification_post_previews(
            post_ids, await self._visibility(viewer_id)
        )
        post_map = {
            post["postId"]: NotificationPostPreview(
                postId=post["postId"],
                content=post.get("content", ""),
                createdAt=post["createdAt"],
            )
            for post in posts
        }

        actor_ids = list({row["actorUserId"] for row in rows})
        actors = await self.user_repository.get_users_by_ids(actor_ids)
        actor_map = {user["userId"]: user for user in actors}

        picture_cache: dict = {}
        items: List[NotificationItem] = []
        for row in rows:
            actor = actor_map.get(row.get("actorUserId"))
            if not actor:
                # The account is gone; skip the row rather than show a blank one.
                continue

            picture, picture_small = await self._resolve_picture_variants(
                actor.get("profilePicture"), picture_cache
            )
            items.append(
                NotificationItem(
                    notificationId=row["notificationId"],
                    type=row["type"],
                    isUnread=row.get("readAt") is None,
                    createdAt=row["createdAt"],
                    actor=PostUserItem(
                        userId=actor.get("userId", ""),
                        username=actor.get("username") or "",
                        name=actor.get("name") or actor.get("username") or "",
                        profilePicture=picture,
                        profilePicture_small=picture_small,
                        bio=actor.get("bio"),
                    ),
                    post=post_map.get(row.get("postId") or ""),
                )
            )
        return items

    @staticmethod
    def _parse_notification_cursor(cursor: Optional[str]) -> Optional[dict]:
        if not cursor:
            return None
        try:
            created_at, notification_id = cursor.split("_")
            return {
                "createdAt": datetime.fromisoformat(created_at),
                "notificationId": notification_id,
            }
        except Exception:
            return None

    async def get_post_quotes(
        self,
        post_id: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        current_user_id: Optional[str] = None,
    ) -> PostPaginationResponse:
        parent = await self.repository.get_post_by_id(post_id)
        if not parent:
            raise PostNotFoundError()
        await self._assert_post_visible(parent, current_user_id)

        quotes = await self.repository.get_post_quotes(
            post_id,
            limit + 1,
            self._parse_post_cursor(cursor),
            await self._visibility(current_user_id),
        )

        has_more = len(quotes) > limit
        if has_more:
            quotes = quotes[:limit]

        next_cursor = None
        if has_more and quotes:
            last = quotes[-1]
            next_cursor = f"{last['createdAt'].isoformat()}_{last['postId']}"

        return PostPaginationResponse(
            data=await self._enrich_posts(quotes, current_user_id),
            meta=PostPaginationMeta(nextCursor=next_cursor, hasMore=has_more),
        )

    async def get_post_reposts(
        self,
        post_id: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        current_user_id: Optional[str] = None,
    ) -> PostUserListResponse:
        if not await self.repository.get_post_by_id(post_id):
            raise PostNotFoundError()

        parent = await self.repository.get_post_by_id(post_id)
        if not parent:
            raise PostNotFoundError()
        await self._assert_post_visible(parent, current_user_id)

        rows = await self.repository.get_post_reposts(
            post_id, limit + 1, self._parse_interaction_cursor(cursor)
        )
        return await self._build_user_list(rows, limit, current_user_id)

    async def get_post_likes(
        self,
        post_id: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        current_user_id: Optional[str] = None,
    ) -> PostUserListResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
        # Who liked a post is only visible to its author.
        if not current_user_id or post.get("userId") != current_user_id:
            raise UnauthorizedActionError()

        rows = await self.repository.get_post_likes(
            post_id, limit + 1, self._parse_interaction_cursor(cursor)
        )
        return await self._build_user_list(rows, limit, current_user_id)

    async def _build_user_list(
        self,
        rows: List[dict],
        limit: int,
        viewer_id: Optional[str] = None,
        apply_hidden: bool = True,
    ) -> PostUserListResponse:
        """Turn interaction rows into a paginated list of the users behind them."""
        # Whoever is hidden from this viewer is left out of the list entirely —
        # except in the block and mute lists, where seeing them is the point.
        if apply_hidden:
            hidden = await self._hidden_author_ids(viewer_id)
            if hidden:
                rows = [row for row in rows if row.get("userId") not in hidden]

        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        next_cursor = None
        if has_more and rows:
            last = rows[-1]
            next_cursor = f"{last['createdAt'].isoformat()}_{str(last['_id'])}"

        if not rows:
            return PostUserListResponse(
                data=[], meta=PostUserListMeta(nextCursor=None, hasMore=False)
            )

        users = await self.user_repository.get_users_by_ids(
            [row["userId"] for row in rows]
        )
        user_map = {user["userId"]: user for user in users}

        # Which of these accounts the viewer already follows, in one query.
        followed: set = set()
        pending: set = set()
        if viewer_id:
            target_ids = [row["userId"] for row in rows]
            followed = set(
                await self.repository.get_followed_ids(viewer_id, target_ids)
            )
            pending = set(
                await self.repository.get_pending_follow_ids(viewer_id, target_ids)
            )

        picture_cache: dict = {}
        items: List[PostUserItem] = []
        for row in rows:
            user = user_map.get(row.get("userId"))
            if not user:
                # The account is gone; skip it rather than show an empty row.
                continue
            picture, picture_small = await self._resolve_picture_variants(
                user.get("profilePicture"), picture_cache
            )
            user_id = user.get("userId", "")
            items.append(
                PostUserItem(
                    userId=user_id,
                    username=user.get("username") or "",
                    name=user.get("name") or user.get("username") or "",
                    profilePicture=picture,
                    profilePicture_small=picture_small,
                    bio=user.get("bio"),
                    isFollowing=user_id in followed,
                    isPending=user_id in pending,
                )
            )

        return PostUserListResponse(
            data=items, meta=PostUserListMeta(nextCursor=next_cursor, hasMore=has_more)
        )

    async def toggle_like(self, post_id: str, user_id: str) -> ToggleResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
        # Likes are refused on a post this viewer may not read.
        await self._assert_post_visible(post, user_id)

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
            await self._notify(post.get("userId"), user_id, "like", post_id)

        return ToggleResponse(status=new_status, count=new_count)

    async def vote_poll(
        self, post_id: str, option_id: str, user_id: str
    ) -> PollResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
        await self._assert_post_visible(post, user_id)

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
        await self._assert_post_visible(post, user_id)

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
            await self._notify(post.get("userId"), user_id, "repost", post_id)

        return ToggleResponse(status=new_status, count=new_count)

    async def toggle_bookmark(self, post_id: str, user_id: str) -> ToggleResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
        await self._assert_post_visible(post, user_id)

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

    async def pin_post(self, post_id: str, user_id: str) -> PostResponse:
        """Pin a post to the top of the caller's profile. One pin per user:
        pinning again silently replaces the previous pin."""
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
        if post["userId"] != user_id:
            raise UnauthorizedActionError()
        if post.get("parentPostId"):
            raise CannotPinReplyError()

        now = datetime.now(timezone.utc)
        await self.repository.pin_post(post_id, user_id, now)
        post["pinnedAt"] = now
        return (await self._enrich_posts([post], user_id))[0]

    async def unpin_post(self, post_id: str, user_id: str) -> PostResponse:
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
        if post["userId"] != user_id:
            raise UnauthorizedActionError()

        await self.repository.unpin_post(post_id)
        post["pinnedAt"] = None
        return (await self._enrich_posts([post], user_id))[0]

    async def set_post_private(
        self, post_id: str, user_id: str, is_private: bool
    ) -> PostResponse:
        """Make a top-level post readable only by its author, or public again.

        A thread is toggled as one unit so no continuation is left behind, and
        replies are excluded because hiding one would break somebody else's chain.
        """
        post = await self.repository.get_post_by_id(post_id)
        if not post:
            raise PostNotFoundError()
        if post["userId"] != user_id:
            raise UnauthorizedActionError()
        if post.get("parentPostId"):
            raise CannotPrivateReplyError()

        await self.repository.set_post_private(post_id, user_id, is_private)
        post["isPrivate"] = is_private
        return (await self._enrich_posts([post], user_id))[0]

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
                "searchTokens": self._extract_search_tokens(data.content),
                "mentions": self._extract_mentions(data.content),
                "isEdited": True,
                "updatedAt": datetime.now(timezone.utc),
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
                # A post the reporter cannot read is reported as "not found",
                # the same answer an unknown id gets, so reporting cannot probe
                # for hidden posts.
                try:
                    await self._assert_post_visible(target, reporter.userId)
                except PostNotFoundError:
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
            now = datetime.now(timezone.utc)
            report_data = {
                "reportId": report_id,
                "targetType": data.targetType,
                "targetId": data.targetId,
                "targetOwnerUserId": owner_id,
                "reporterUserId": reporter.userId,
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

    async def _resolve_picture_variants(
        self, raw: Optional[str], cache: dict
    ) -> tuple[Optional[str], Optional[str]]:
        """Resolve a stored picture path to (full, small) URLs, cached per request."""
        if not raw:
            return None, None
        if raw in cache:
            return cache[raw]
        try:
            full = await self.storage_service.resolve_url(raw)
            small = await self.storage_service.resolve_url(raw, variant="small")
        except Exception as e:
            logger.error(f"Failed to resolve picture {raw}: {str(e)}")
            full, small = None, None
        cache[raw] = (full, small)
        return full, small

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
                    target_username = (owner or {}).get("username")
                    target_display_name = (owner or {}).get("name")
                    raw_picture = (owner or {}).get("profilePicture")
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
            reporter_username = (reporter or {}).get("username")

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

        # Keep a thread connected when a middle segment is deleted: its own next
        # segment takes its place, so the chain still reads 1..N without a gap.
        continuation = await self.repository.get_self_continuation(
            post_id, post["userId"]
        )
        if continuation:
            parent_id = post.get("parentPostId")
            await self.repository.relink_continuation(
                continuation["postId"], parent_id, post.get("depth", 0)
            )
            if parent_id is None:
                # The deleted post led the thread; the continuation leads it now.
                await self.repository.repoint_thread_root(
                    post_id, continuation["postId"], post["userId"]
                )
            else:
                # The continuation now answers what the deleted post answered.
                await self.repository.increment_post_stats(parent_id, "replyCount", 1)

        await self.repository.delete_post(post_id)
        await self.repository.delete_poll_votes(post_id)

        if post.get("parentPostId"):
            await self.repository.increment_post_stats(
                post["parentPostId"], "replyCount", -1
            )

    async def _resolve_user_id(self, username: str) -> str:
        """Map a profile username to the immutable userId every post query uses."""
        user = await self.user_repository.find_one({"username": username.lower()})
        if not user:
            raise UserProfileNotFoundError()
        return user.get("userId", "")

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

        target_user_id = await self._resolve_user_id(target_username)
        visibility = await self._visibility(current_user_id)

        # The pinned post leads the plain post list. It may be an old post, so it
        # is fetched separately and kept out of *every* page — otherwise it would
        # be shown once on top and again wherever it falls in the pagination.
        pinned_post = None
        if media is None:
            pinned_post = await self.repository.get_pinned_post(
                target_user_id, visibility
            )
        pinned_id = pinned_post["postId"] if pinned_post else None

        # One row decides `has_more`; one more absorbs the pinned post if it lands
        # inside this window.
        fetch = limit + 1 + (1 if pinned_id else 0)
        posts = await self.repository.get_user_posts(
            target_user_id, fetch, cursor_dict, media, visibility
        )
        if pinned_id:
            posts = [p for p in posts if p["postId"] != pinned_id]

        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]

        next_cursor = None
        if has_more and posts:
            last_post = posts[-1]
            next_cursor = f"{last_post['createdAt'].isoformat()}_{last_post['postId']}"

        enriched_posts = await self._enrich_posts(posts, current_user_id)
        # Only the first page carries the pin above the regular list.
        if pinned_post and cursor_dict is None:
            pinned = await self._enrich_posts([pinned_post], current_user_id)
            enriched_posts = [*pinned, *enriched_posts]

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
            await self._resolve_user_id(target_username),
            limit + 1,
            cursor_dict,
            await self._visibility(current_user_id),
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
            user_id, limit + 1, cursor_dict, await self._visibility(user_id)
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

        result = await self.repository.get_user_likes(
            user_id, limit + 1, cursor_dict, await self._visibility(user_id)
        )
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

    async def get_user_profile(
        self, username: str, current_user_id: Optional[str] = None
    ) -> Page48UserProfileResponse:
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

        raw_banner = user.get("bannerPicture")
        banner_picture = None
        banner_picture_medium = None
        banner_picture_small = None
        banner_blur_hash = user.get("bannerBlurHash")

        if raw_banner:
            try:
                banner_picture = await self.storage_service.resolve_url(raw_banner)
                banner_picture_medium = await self.storage_service.resolve_url(
                    raw_banner, variant="medium"
                )
                banner_picture_small = await self.storage_service.resolve_url(
                    raw_banner, variant="small"
                )
            except Exception as e:
                logger.error(f"Failed to resolve banner for {username}: {str(e)}")

        owner_id = user.get("userId", "")
        # Relationship to the viewer, checked once and only for someone else.
        is_blocked = False
        is_blocked_by = False
        is_muted = False
        if current_user_id and current_user_id != owner_id:
            is_blocked = bool(
                await self.repository.get_block(current_user_id, owner_id)
            )
            is_blocked_by = bool(
                await self.repository.get_block(owner_id, current_user_id)
            )
            is_muted = bool(await self.repository.get_mute(current_user_id, owner_id))

        post_count = await self.repository.count_user_posts(owner_id)
        repost_count = await self.repository.count_user_reposts(owner_id)
        # Counted live: no stored counter that can drift out of sync.
        follower_count = await self.repository.count_followers(owner_id)
        following_count = await self.repository.count_following(owner_id)

        is_self = bool(current_user_id) and current_user_id == owner_id
        is_following = False
        is_follow_pending = False
        if current_user_id and not is_self:
            relation = await self.repository.get_follow(current_user_id, owner_id)
            if relation:
                is_follow_pending = relation.get("status") == "pending"
                is_following = not is_follow_pending

        return Page48UserProfileResponse(
            userId=owner_id,
            name=user.get("name") or stored_username,
            username=stored_username,
            bio=user.get("bio"),
            profilePicture=profile_picture,
            profilePicture_medium=profile_picture_medium,
            profilePicture_small=profile_picture_small,
            blurHash=blur_hash,
            bannerPicture=banner_picture,
            bannerPicture_medium=banner_picture_medium,
            bannerPicture_small=banner_picture_small,
            bannerBlurHash=banner_blur_hash,
            postCount=post_count,
            repostCount=repost_count,
            isBlocked=is_blocked,
            isBlockedBy=is_blocked_by,
            isMuted=is_muted,
            isLocked=bool(user.get("page48Locked")),
            isFollowPending=is_follow_pending,
            followerCount=follower_count,
            followingCount=following_count,
            isFollowing=is_following,
        )

    # Follows
    async def _resolve_follow_target(self, username: str) -> dict:
        user = await self.user_repository.find_one({"username": username.lower()})
        if not user:
            raise UserProfileNotFoundError()
        return user

    async def follow_user(self, username: str, current_user_id: str) -> FollowResponse:
        target = await self._resolve_follow_target(username)
        target_id = target.get("userId", "")
        if not target_id or target_id == current_user_id:
            raise CannotFollowSelfError()

        # A block severs the relationship both ways; following through it would
        # undo the block from one side behind the blocker's back.
        if await self.repository.get_block(current_user_id, target_id):
            raise UnauthorizedActionError()
        if await self.repository.get_block(target_id, current_user_id):
            raise UnauthorizedActionError()

        # A locked account turns a follow into a request its owner must approve.
        locked = bool(target.get("page48Locked"))
        row = await self.repository.get_follow(current_user_id, target_id)
        if not row:
            status = "pending" if locked else "accepted"
            try:
                await self.repository.insert_follow(current_user_id, target_id, status)
            except DuplicateKeyError:
                # Two taps raced; read back whatever the other request stored.
                row = await self.repository.get_follow(current_user_id, target_id)
                status = (row or {}).get("status", "accepted")
            else:
                await self._notify(
                    target_id,
                    current_user_id,
                    "followRequest" if status == "pending" else "follow",
                )
        else:
            status = row.get("status", "accepted")

        return FollowResponse(
            isFollowing=status != "pending",
            isPending=status == "pending",
            followerCount=await self.repository.count_followers(target_id),
        )

    async def unfollow_user(
        self, username: str, current_user_id: str
    ) -> FollowResponse:
        target = await self._resolve_follow_target(username)
        target_id = target.get("userId", "")
        if not target_id or target_id == current_user_id:
            raise CannotFollowSelfError()

        row = await self.repository.get_follow(current_user_id, target_id)
        await self.repository.delete_follow(current_user_id, target_id)
        # Cancelling a request has to clear the owner's Follows tab entry too.
        if row and row.get("status") == "pending":
            await self.repository.delete_notifications(
                target_id, current_user_id, ["followRequest"]
            )
        return FollowResponse(
            isFollowing=False,
            isPending=False,
            followerCount=await self.repository.count_followers(target_id),
        )

    async def accept_follow_request(
        self, username: str, current_user_id: str
    ) -> FollowResponse:
        """Approve `username`'s pending request to follow the current user."""
        requester = await self._resolve_follow_target(username)
        requester_id = requester.get("userId", "")
        if not requester_id or requester_id == current_user_id:
            raise CannotFollowSelfError()

        row = await self.repository.get_follow(requester_id, current_user_id)
        if row and row.get("status") == "pending":
            await self.repository.update_follow_status(
                requester_id, current_user_id, "accepted"
            )
            await self.repository.delete_notifications(
                current_user_id, requester_id, ["followRequest"]
            )
            # Let the new follower know the request went through.
            await self._notify(requester_id, current_user_id, "followAccepted")
        return FollowResponse(
            isFollowing=True,
            followerCount=await self.repository.count_followers(current_user_id),
        )

    async def decline_follow_request(
        self, username: str, current_user_id: str
    ) -> FollowResponse:
        """Turn down `username`'s pending request to follow the current user."""
        requester = await self._resolve_follow_target(username)
        requester_id = requester.get("userId", "")
        if not requester_id or requester_id == current_user_id:
            raise CannotFollowSelfError()

        row = await self.repository.get_follow(requester_id, current_user_id)
        if row and row.get("status") == "pending":
            await self.repository.delete_follow(requester_id, current_user_id)
            await self.repository.delete_notifications(
                current_user_id, requester_id, ["followRequest"]
            )
        return FollowResponse(
            isFollowing=False,
            followerCount=await self.repository.count_followers(current_user_id),
        )

    async def update_page48_settings(
        self, current_user_id: str, locked: bool
    ) -> Page48SettingsResponse:
        """Lock or unlock this account's Page48 posts (follower-only when locked)."""
        await self.user_repository.set_page48_locked(current_user_id, locked)
        # What this account may see no longer depends on who it follows.
        self._hidden_authors = None
        return Page48SettingsResponse(locked=locked)

    async def block_user(self, username: str, current_user_id: str) -> BlockResponse:
        """Block: mutual silence, and the follow between them is severed."""
        target = await self._resolve_follow_target(username)
        target_id = target.get("userId", "")
        if not target_id or target_id == current_user_id:
            raise CannotBlockSelfError()

        if not await self.repository.get_block(current_user_id, target_id):
            try:
                await self.repository.insert_block(current_user_id, target_id)
            except DuplicateKeyError:
                # Two taps raced; the block already exists.
                pass
            await self.repository.delete_follow(current_user_id, target_id)
            await self.repository.delete_follow(target_id, current_user_id)

        # The cached hidden set no longer matches.
        self._hidden_authors = None
        return BlockResponse(isBlocked=True)

    async def unblock_user(self, username: str, current_user_id: str) -> BlockResponse:
        target = await self._resolve_follow_target(username)
        target_id = target.get("userId", "")
        if not target_id or target_id == current_user_id:
            raise CannotBlockSelfError()

        await self.repository.delete_block(current_user_id, target_id)
        self._hidden_authors = None
        return BlockResponse(isBlocked=False)

    async def mute_user(self, username: str, current_user_id: str) -> MuteResponse:
        """Mute only removes someone from the timeline."""
        target = await self._resolve_follow_target(username)
        target_id = target.get("userId", "")
        if not target_id or target_id == current_user_id:
            raise CannotMuteSelfError()

        if not await self.repository.get_mute(current_user_id, target_id):
            try:
                await self.repository.insert_mute(current_user_id, target_id)
            except DuplicateKeyError:
                pass

        return MuteResponse(isMuted=True)

    async def unmute_user(self, username: str, current_user_id: str) -> MuteResponse:
        target = await self._resolve_follow_target(username)
        target_id = target.get("userId", "")
        if not target_id or target_id == current_user_id:
            raise CannotMuteSelfError()

        await self.repository.delete_mute(current_user_id, target_id)
        return MuteResponse(isMuted=False)

    async def get_blocked_users(
        self,
        current_user_id: str,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> PostUserListResponse:
        rows = await self.repository.get_blocked_users(
            current_user_id, limit + 1, self._parse_interaction_cursor(cursor)
        )
        return await self._build_user_list(rows, limit, current_user_id, False)

    async def get_muted_users(
        self,
        current_user_id: str,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> PostUserListResponse:
        rows = await self.repository.get_muted_users(
            current_user_id, limit + 1, self._parse_interaction_cursor(cursor)
        )
        return await self._build_user_list(rows, limit, current_user_id, False)

    async def get_followers(
        self,
        username: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        current_user_id: Optional[str] = None,
    ) -> PostUserListResponse:
        """Accounts that follow this user."""
        user = await self._resolve_follow_target(username)
        rows = await self.repository.get_follow_edges(
            "followingId",
            user.get("userId", ""),
            limit + 1,
            self._parse_interaction_cursor(cursor),
        )
        return await self._build_user_list(
            self._as_user_rows(rows, "followerId"), limit, current_user_id
        )

    async def get_following(
        self,
        username: str,
        limit: int = 20,
        cursor: Optional[str] = None,
        current_user_id: Optional[str] = None,
    ) -> PostUserListResponse:
        """Accounts this user follows."""
        user = await self._resolve_follow_target(username)
        rows = await self.repository.get_follow_edges(
            "followerId",
            user.get("userId", ""),
            limit + 1,
            self._parse_interaction_cursor(cursor),
        )
        return await self._build_user_list(
            self._as_user_rows(rows, "followingId"), limit, current_user_id
        )

    @staticmethod
    def _as_user_rows(rows: List[dict], user_field: str) -> List[dict]:
        """Reshape follow edges into the shape `_build_user_list` expects."""
        return [
            {
                "userId": row.get(user_field, ""),
                "createdAt": row["createdAt"],
                "_id": row["_id"],
            }
            for row in rows
        ]

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
            user["userId"],
            limit + 1,
            cursor_dict,
            await self._visibility(current_user_id),
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
