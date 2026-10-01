from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


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


class EditPostRequest(BaseModel):
    content: str = Field(..., max_length=500)
    tags: list[str] = Field(default_factory=list)


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

    content: str
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


class Page48UserProfileResponse(BaseModel):
    userId: str
    name: str
    username: str
    bio: Optional[str] = None
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

    # Counted live from the follow edges; there is no stored counter to drift.
    followerCount: int = 0
    followingCount: int = 0
    # Whether the requesting user follows this profile (false for guests/self).
    isFollowing: bool = False


class FollowResponse(BaseModel):
    isFollowing: bool
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


class AdminReportPaginationMeta(BaseModel):
    nextCursor: Optional[str] = None
    hasMore: bool = False
    total: int = 0


class AdminReportPaginationResponse(BaseModel):
    data: list[AdminReportItem]
    meta: AdminReportPaginationMeta


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
    # Whether the requesting user already follows this account.
    isFollowing: bool = False


class PostUserListMeta(BaseModel):
    nextCursor: Optional[str] = None
    hasMore: bool = False


class PostUserListResponse(BaseModel):
    data: list[PostUserItem]
    meta: PostUserListMeta


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


# `quotedPost` refers to `PostResponse` from inside its own definition, so the
# forward reference is resolved once the module has finished loading.
PostResponse.model_rebuild()
