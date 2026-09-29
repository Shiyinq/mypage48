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


class CreatePostRequest(BaseModel):
    content: str = Field(..., max_length=500)
    images: list[str] = Field(default_factory=list, max_length=4)  # max 4 filenames
    parentPostId: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    videos: list[VideoRef] = Field(default_factory=list, max_length=1)


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
    
    likesCount: int = 0
    repostCount: int = 0
    bookmarksCount: int = 0
    
    isEdited: bool = False
    createdAt: datetime
    updatedAt: datetime
    
    # Context for current user (optional, returned if user is logged in)
    isLiked: Optional[bool] = False
    isReposted: Optional[bool] = False
    isBookmarked: Optional[bool] = False

    # Populated when the post is returned as a user's repost
    repostedAt: Optional[datetime] = None


class Page48UserProfileResponse(BaseModel):
    userId: str
    name: str
    username: str
    bio: Optional[str] = None
    profilePicture: Optional[str] = None
    profilePicture_medium: Optional[str] = None
    profilePicture_small: Optional[str] = None
    blurHash: Optional[str] = None
    postCount: int = 0
    repostCount: int = 0


class TrendingTag(BaseModel):
    tag: str
    count: int = 0


class TrendingTagsResponse(BaseModel):
    tags: list[TrendingTag] = []


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


class ToggleResponse(BaseModel):
    status: bool
    count: int
