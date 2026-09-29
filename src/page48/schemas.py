from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Page48Image(BaseModel):
    filename: str
    url: Optional[str] = None
    url_medium: Optional[str] = None
    url_small: Optional[str] = None
    blurHash: Optional[str] = None
    width: Optional[int] = 0
    height: Optional[int] = 0


class CreatePostRequest(BaseModel):
    content: str = Field(..., max_length=500)
    images: list[str] = Field(default_factory=list, max_length=4)  # max 4 filenames
    parentPostId: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


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
