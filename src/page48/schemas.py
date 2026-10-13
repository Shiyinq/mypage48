from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# Who may reply to a post. The author always may, whatever the setting is.
# - everyone: any signed-in account
# - following: accounts the author follows
# - followers: accounts that follow the author
# - following_and_followers: either of the two above
# - only_me: the author alone (no external replies)
# - mentioned: accounts named with `@` in the post
ReplySetting = Literal[
    "everyone",
    "following",
    "followers",
    "following_and_followers",
    "only_me",
    "mentioned",
]


class Page48Image(BaseModel):
    filename: str
    url: Optional[str] = None
    url_medium: Optional[str] = None
    url_small: Optional[str] = None
    blurHash: Optional[str] = None
    width: Optional[int] = 0
    height: Optional[int] = 0


class ImageRef(BaseModel):
    """A reference to an already-uploaded image, sent when creating a post."""

    filename: str
    width: Optional[int] = 0
    height: Optional[int] = 0


class VideoRef(BaseModel):
    """A reference to an already-uploaded video, sent when creating a post."""

    filename: str
    width: Optional[int] = 0
    height: Optional[int] = 0
    duration: Optional[float] = 0.0


class Page48Video(BaseModel):
    filename: str
    url: Optional[str] = None
    width: Optional[int] = 0
    height: Optional[int] = 0
    duration: Optional[float] = 0.0


class MediaRef(BaseModel):
    """One ordered media item, sent when creating or editing a post."""

    type: Literal["image", "video"]
    filename: str
    width: Optional[int] = 0
    height: Optional[int] = 0
    duration: Optional[float] = 0.0


class Page48Media(BaseModel):
    """One resolved media item, in the order the author posted it."""

    type: Literal["image", "video"]
    filename: str
    url: Optional[str] = None
    url_medium: Optional[str] = None
    url_small: Optional[str] = None
    blurHash: Optional[str] = None
    width: Optional[int] = 0
    height: Optional[int] = 0
    duration: Optional[float] = 0.0


class VideoUploadResponse(BaseModel):
    filename: str
    url: Optional[str] = None
    width: Optional[int] = 0
    height: Optional[int] = 0
    duration: Optional[float] = 0.0


class CreatePollRequest(BaseModel):
    """Poll attached to a new post. The post content acts as the question."""

    options: list[str] = Field(default_factory=list, max_length=10)


class PollOptionResponse(BaseModel):
    id: str
    text: str
    votes: int = 0


class PollResponse(BaseModel):
    options: list[PollOptionResponse] = []
    totalVotes: int = 0
    endsAt: datetime
    isExpired: bool = False
    # Option picked by the requesting user, if any.
    myOptionId: Optional[str] = None


class VotePollRequest(BaseModel):
    optionId: str = Field(..., min_length=1, max_length=32)


class ThreadPostItem(BaseModel):
    """One post of a thread, chained to the item before it."""

    content: str = Field(..., max_length=500)
    images: list[ImageRef] = Field(default_factory=list, max_length=10)
    videos: list[VideoRef] = Field(default_factory=list, max_length=1)
    poll: Optional[CreatePollRequest] = None
    tags: list[str] = Field(default_factory=list)
    # Each thread post may quote its own post, exactly like a standalone one.
    quotedPostId: Optional[str] = None
    # Hide this post's content behind a spoiler gate until the reader opts in.
    isSpoiler: bool = False
    # Ordered media (images and videos mixed), up to `MAX_MEDIA` items.
    media: list[MediaRef] = Field(default_factory=list)
    # Who may reply to this item. Each thread post carries its own setting.
    replySettings: ReplySetting = "everyone"


class CreateThreadRequest(BaseModel):
    """A chain of posts published together, each replying to the previous one."""

    posts: list[ThreadPostItem] = Field(default_factory=list, max_length=50)


class CreatePostRequest(BaseModel):
    content: str = Field(..., max_length=500)
    images: list[ImageRef] = Field(default_factory=list, max_length=10)
    parentPostId: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    videos: list[VideoRef] = Field(default_factory=list, max_length=1)
    poll: Optional[CreatePollRequest] = None
    # When set, this post quotes the referenced post: it is a normal post of
    # its own that embeds a read-only preview of the quoted one.
    quotedPostId: Optional[str] = None
    # Hide this post's content behind a spoiler gate until the reader opts in.
    isSpoiler: bool = False
    # Ordered media (images and videos mixed), up to `MAX_MEDIA` items.
    media: list[MediaRef] = Field(default_factory=list)
    # Who may reply to this post.
    replySettings: ReplySetting = "everyone"


class EditPostRequest(BaseModel):
    content: str = Field(..., max_length=500)
    tags: list[str] = Field(default_factory=list)
    # None leaves the current spoiler flag untouched.
    isSpoiler: Optional[bool] = None
    # None leaves the current media untouched; a list (even empty) replaces it.
    images: Optional[list[ImageRef]] = None
    videos: Optional[list[VideoRef]] = None
    # Ordered media (images and videos mixed). Preferred over images/videos.
    media: Optional[list[MediaRef]] = None
    # None leaves the current reply setting untouched.
    replySettings: Optional[ReplySetting] = None


class PostResponse(BaseModel):
    postId: str
    rootPostId: Optional[str] = None
    parentPostId: Optional[str] = None
    depth: int = 0
    replyCount: int = 0

    userId: str
    username: str
    userDisplayName: str
    userProfilePicture: Optional[str] = None
    userProfilePicture_small: Optional[str] = None
    userBlurHash: Optional[str] = None
    # Page48-only account badge: "official_account" or "page48_admin".
    page48AccountType: Optional[str] = None

    content: str
    # Ordered media as posted; `images`/`videos` below stay as convenient views.
    media: list[Page48Media] = []
    images: list[Page48Image] = []
    videos: list[Page48Video] = []
    tags: list[str] = []
    poll: Optional[PollResponse] = None

    # Total number of posts in the thread starting at this post (itself included).
    # 0 means the post is not a thread.
    threadCount: int = 0

    likesCount: int = 0
    repostCount: int = 0
    quoteCount: int = 0
    bookmarksCount: int = 0

    isEdited: bool = False
    createdAt: datetime
    updatedAt: datetime

    # Set only on a user's own profile when they pinned this post.
    isPinned: bool = False

    # True when only the author can read this post (hidden from everyone else).
    isPrivate: bool = False

    # True when the content is hidden behind a spoiler gate in the UI. Purely a
    # display flag: everyone can still read the post, they just have to reveal it.
    isSpoiler: bool = False

    # Who may reply to this post.
    replySettings: ReplySetting = "everyone"
    # Whether the requesting viewer may reply (the author always may).
    canReply: bool = True

    # Context for current user (optional, returned if user is logged in)
    isLiked: Optional[bool] = False
    isReposted: Optional[bool] = False
    isBookmarked: Optional[bool] = False

    # Populated when the post is returned as a user's repost
    repostedAt: Optional[datetime] = None

    # A read-only preview of the post this one quotes, if any. Never nested
    # more than one level deep.
    quotedPost: Optional["PostResponse"] = None
    # Kept alongside the preview so a deleted original can still be detected.
    quotedPostId: Optional[str] = None

    # The post this one replies to, attached only on a profile's Replies tab so
    # the reply keeps its context. Never nested more than one level deep.
    repliedToPost: Optional["PostResponse"] = None


class Page48UserProfileResponse(BaseModel):
    userId: str
    name: str
    username: str
    bio: Optional[str] = None
    # Page48-only account badge: "official_account" or "page48_admin".
    page48AccountType: Optional[str] = None
    profilePicture: Optional[str] = None
    profilePicture_medium: Optional[str] = None
    profilePicture_small: Optional[str] = None
    blurHash: Optional[str] = None
    bannerPicture: Optional[str] = None
    bannerPicture_medium: Optional[str] = None
    bannerPicture_small: Optional[str] = None
    bannerBlurHash: Optional[str] = None
    postCount: int = 0
    repostCount: int = 0
    # How the requesting viewer stands with this account.
    isBlocked: bool = False
    isBlockedBy: bool = False
    isMuted: bool = False

    # Counted live from the follow edges; there is no stored counter to drift.
    followerCount: int = 0
    followingCount: int = 0
    # Whether the requesting user follows this profile (false for guests/self).
    isFollowing: bool = False
    # Whether the requesting user has an unanswered follow request pending.
    isFollowPending: bool = False
    # True when this account only shows its posts to approved followers.
    isLocked: bool = False
    # True when this account is Page48-banned (hidden, read-only).
    isBanned: bool = False
    # When a timed ban lapses; null means the ban is permanent.
    bannedUntil: Optional[datetime] = None


class Page48SettingsRequest(BaseModel):
    """The Page48-only toggles, kept apart from the MyPage48 `isPublic` stat."""

    locked: bool


class Page48SettingsResponse(BaseModel):
    locked: bool = False


class FollowResponse(BaseModel):
    isFollowing: bool
    # True when the target only accepts followers, so this is a request.
    isPending: bool = False
    followerCount: int = 0


class TrendingTag(BaseModel):
    tag: str
    count: int = 0


class TrendingTagsResponse(BaseModel):
    tags: list[TrendingTag] = []


class ActiveUserItem(BaseModel):
    userId: str
    username: str
    name: str
    profilePicture: Optional[str] = None
    page48AccountType: Optional[str] = None
    postCount: int = 0
    lastPostedAt: Optional[datetime] = None


class ActiveUsersResponse(BaseModel):
    users: list[ActiveUserItem] = []


ReportTargetType = Literal["post", "user"]
ReportReason = Literal["spam", "harassment", "inappropriate", "other"]


class ReportCreate(BaseModel):
    targetType: ReportTargetType
    targetId: str
    reason: ReportReason
    note: Optional[str] = Field(default=None, max_length=500)


class ReportResponse(BaseModel):
    reportId: str
    targetType: ReportTargetType
    targetId: str
    reason: ReportReason
    note: Optional[str] = None
    status: str = "pending"
    createdAt: datetime


class AdminReportItem(BaseModel):
    reportId: str
    targetType: ReportTargetType
    targetId: str
    reason: ReportReason
    note: Optional[str] = None
    status: str = "pending"
    createdAt: datetime

    reporterUserId: str
    reporterUsername: Optional[str] = None

    # Target preview (post content or reported user profile).
    targetExists: bool = True
    targetUsername: Optional[str] = None
    targetDisplayName: Optional[str] = None
    targetContent: Optional[str] = None
    targetImageCount: int = 0
    targetProfilePicture: Optional[str] = None


class AdminReportReporter(BaseModel):
    userId: str
    username: Optional[str] = None
    reason: ReportReason
    note: Optional[str] = None
    status: str = "pending"
    createdAt: datetime


class AdminReportGroup(BaseModel):
    """One reported target, with every report against it collapsed in."""

    targetType: ReportTargetType
    targetId: str
    reportCount: int = 0
    reasons: list[str] = []
    status: str = "pending"
    note: Optional[str] = None
    latestAt: datetime

    # Target preview (post content or reported user profile).
    targetExists: bool = True
    targetUserId: Optional[str] = None
    targetUsername: Optional[str] = None
    targetDisplayName: Optional[str] = None
    targetContent: Optional[str] = None
    targetImageCount: int = 0
    targetProfilePicture: Optional[str] = None

    # Reporters, capped server-side for display.
    reporters: list[AdminReportReporter] = []


class AdminReportPaginationMeta(BaseModel):
    nextCursor: Optional[str] = None
    hasMore: bool = False
    total: int = 0
    totalReports: int = 0


class AdminReportPaginationResponse(BaseModel):
    data: list[AdminReportGroup]
    meta: AdminReportPaginationMeta


BanDuration = Literal["permanent", "7d", "30d"]


class BanUserRequest(BaseModel):
    duration: BanDuration = "permanent"
    reason: Optional[str] = Field(default=None, max_length=500)


class BannedUserItem(BaseModel):
    userId: str
    username: Optional[str] = None
    displayName: Optional[str] = None
    profilePicture: Optional[str] = None
    bannedAt: Optional[datetime] = None
    bannedUntil: Optional[datetime] = None
    bannedByUsername: Optional[str] = None
    reason: Optional[str] = None


class BannedUserPaginationMeta(BaseModel):
    total: int = 0
    hasMore: bool = False


class BannedUserPaginationResponse(BaseModel):
    data: list[BannedUserItem]
    meta: BannedUserPaginationMeta


class ThreadResponse(BaseModel):
    post: PostResponse
    replies: list["ThreadResponse"] = []


class PostPaginationMeta(BaseModel):
    nextCursor: Optional[str] = None
    hasMore: bool = False


class PostPaginationResponse(BaseModel):
    data: list[PostResponse]
    meta: PostPaginationMeta


class PostUserItem(BaseModel):
    """A user shown in an interaction list (reposts / likes / followers)."""

    userId: str
    username: str
    name: str
    profilePicture: Optional[str] = None
    profilePicture_small: Optional[str] = None
    bio: Optional[str] = None
    page48AccountType: Optional[str] = None
    # Whether the requesting user already follows this account.
    isFollowing: bool = False
    # Whether the requesting user has an unanswered follow request pending.
    isPending: bool = False


class PostUserListMeta(BaseModel):
    nextCursor: Optional[str] = None
    hasMore: bool = False


class PostUserListResponse(BaseModel):
    data: list[PostUserItem]
    meta: PostUserListMeta


class BlockResponse(BaseModel):
    isBlocked: bool = False


class MuteResponse(BaseModel):
    isMuted: bool = False


class SearchTopResponse(BaseModel):
    """The overview tab of search: a few people, tags, then the newest posts."""

    users: list[PostUserItem] = []
    tags: list[TrendingTag] = []
    posts: list[PostResponse] = []


class PostActivityResponse(BaseModel):
    """Everything the post activity page needs for its header and tabs."""

    post: PostResponse
    quoteCount: int = 0
    repostCount: int = 0
    likeCount: int = 0
    # Likes are only visible to the author of the post.
    canViewLikes: bool = False


class ToggleResponse(BaseModel):
    status: bool
    count: int


class CreateThreadResponse(BaseModel):
    rootPostId: str
    posts: list[PostResponse] = []


NotificationType = Literal[
    "reply",
    "mention",
    "follow",
    "followRequest",
    "followAccepted",
    "like",
    "repost",
    "quote",
]


class NotificationPostPreview(BaseModel):
    """Just what a notification snippet renders.

    The full post payload would resolve and sign every media URL for a preview
    that only ever shows the text, so notifications deliberately carry this.
    """

    postId: str
    content: str
    createdAt: datetime
    isSpoiler: bool = False


class NotificationItem(BaseModel):
    """One entry of the notifications feed."""

    notificationId: str
    type: NotificationType
    isUnread: bool = False
    createdAt: datetime

    # Identity is read live from the user document, never copied onto the
    # notification: a rename or a new picture shows up immediately.
    actor: PostUserItem
    # The post to preview and open. Absent for follows, and for posts that no
    # longer exist (the client renders those as unavailable).
    post: Optional[NotificationPostPreview] = None


class NotificationPaginationMeta(BaseModel):
    nextCursor: Optional[str] = None
    hasMore: bool = False


class NotificationPaginationResponse(BaseModel):
    data: list[NotificationItem]
    meta: NotificationPaginationMeta


class NotificationTabSummary(BaseModel):
    """One row of the notifications overview: unread count plus a preview."""

    tab: str
    count: int = 0
    previews: list[NotificationItem] = []


class NotificationOverviewResponse(BaseModel):
    total: int = 0
    tabs: list[NotificationTabSummary] = []


class NotificationCountsResponse(BaseModel):
    """Unread notifications of one recipient, per tab plus the overall total."""

    total: int = 0
    replies: int = 0
    mentions: int = 0
    likes: int = 0
    reposts: int = 0
    follows: int = 0


class MarkNotificationsReadResponse(BaseModel):
    count: int = 0


# `quotedPost` refers to `PostResponse` from inside its own definition, so the
# forward reference is resolved once the module has finished loading.
PostResponse.model_rebuild()
