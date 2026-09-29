from typing import Optional
from fastapi import APIRouter, Depends, Query, Path

from src.auth.schemas import UserCurrent
from src.dependencies import (
    get_current_user,
    get_current_user_optional,
    require_admin,
    require_csrf_protection,
)
from src.page48.schemas import (
    CreatePostRequest,
    EditPostRequest,
    Page48UserProfileResponse,
    PostPaginationResponse,
    PostResponse,
    ThreadResponse,
    ToggleResponse,
    TrendingTagsResponse,
)
from src.page48.service import Page48Service
from src.dependencies import get_page48_service

router = APIRouter()


@router.get("/feed", response_model=PostPaginationResponse)
async def get_feed(
    limit: int = Query(20, le=50),
    cursor: Optional[str] = None,
    media: Optional[str] = Query(
        None, pattern="^(text|image|video)$", description="Filter by media type"
    ),
    current_user: Optional[UserCurrent] = Depends(get_current_user_optional),
    service: Page48Service = Depends(get_page48_service),
):
    user_id = current_user.userId if current_user else None
    return await service.get_feed(limit, cursor, user_id, media)


@router.get("/posts/{postId}", response_model=PostResponse)
async def get_post(
    postId: str = Path(...),
    current_user: Optional[UserCurrent] = Depends(get_current_user_optional),
    service: Page48Service = Depends(get_page48_service),
):
    user_id = current_user.userId if current_user else None
    return await service.get_post(postId, user_id)


@router.get("/posts/{postId}/thread", response_model=ThreadResponse)
async def get_thread(
    postId: str = Path(...),
    current_user: Optional[UserCurrent] = Depends(get_current_user_optional),
    service: Page48Service = Depends(get_page48_service),
):
    user_id = current_user.userId if current_user else None
    return await service.get_thread(postId, user_id)


@router.get("/posts/{postId}/replies", response_model=PostPaginationResponse)
async def get_direct_replies(
    postId: str = Path(...),
    limit: int = Query(20, le=50),
    cursor: Optional[str] = None,
    current_user: Optional[UserCurrent] = Depends(get_current_user_optional),
    service: Page48Service = Depends(get_page48_service),
):
    user_id = current_user.userId if current_user else None
    return await service.get_direct_replies(postId, limit, cursor, user_id)


@router.get("/users/{username}/posts", response_model=PostPaginationResponse)
async def get_user_posts(
    username: str = Path(...),
    limit: int = Query(20, le=50),
    cursor: Optional[str] = None,
    media: Optional[str] = Query(
        None, pattern="^(text|image|video)$", description="Filter by media type"
    ),
    current_user: Optional[UserCurrent] = Depends(get_current_user_optional),
    service: Page48Service = Depends(get_page48_service),
):
    user_id = current_user.userId if current_user else None
    return await service.get_user_posts(username, limit, cursor, user_id, media)


@router.get("/users/{username}/replies", response_model=PostPaginationResponse)
async def get_user_replies(
    username: str = Path(...),
    limit: int = Query(20, le=50),
    cursor: Optional[str] = None,
    current_user: Optional[UserCurrent] = Depends(get_current_user_optional),
    service: Page48Service = Depends(get_page48_service),
):
    user_id = current_user.userId if current_user else None
    return await service.get_user_replies(username, limit, cursor, user_id)


@router.get("/users/{username}/profile", response_model=Page48UserProfileResponse)
async def get_user_profile(
    username: str = Path(...),
    service: Page48Service = Depends(get_page48_service),
):
    return await service.get_user_profile(username)


@router.get("/users/{username}/reposts", response_model=PostPaginationResponse)
async def get_user_reposts(
    username: str = Path(...),
    limit: int = Query(20, le=50),
    cursor: Optional[str] = None,
    current_user: Optional[UserCurrent] = Depends(get_current_user_optional),
    service: Page48Service = Depends(get_page48_service),
):
    user_id = current_user.userId if current_user else None
    return await service.get_user_reposts(username, limit, cursor, user_id)


@router.get("/tags/trending", response_model=TrendingTagsResponse)
async def get_trending_tags(
    limit: int = Query(10, ge=1, le=50),
    service: Page48Service = Depends(get_page48_service),
):
    return await service.get_trending_tags(limit)


@router.get("/tags/{tag}/posts", response_model=PostPaginationResponse)
async def get_posts_by_tag(
    tag: str = Path(...),
    limit: int = Query(20, le=50),
    cursor: Optional[str] = None,
    media: Optional[str] = Query(
        None, pattern="^(text|image|video)$", description="Filter by media type"
    ),
    current_user: Optional[UserCurrent] = Depends(get_current_user_optional),
    service: Page48Service = Depends(get_page48_service),
):
    user_id = current_user.userId if current_user else None
    return await service.get_posts_by_tag(tag, limit, cursor, user_id, media)


# Authenticated routes
@router.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(
    request: CreatePostRequest,
    current_user: UserCurrent = Depends(get_current_user),
    _: bool = Depends(require_csrf_protection),
    service: Page48Service = Depends(get_page48_service),
):
    return await service.create_post(request, current_user)


@router.delete("/posts/{postId}")
async def delete_post(
    postId: str = Path(...),
    current_user: UserCurrent = Depends(get_current_user),
    _: bool = Depends(require_csrf_protection),
    service: Page48Service = Depends(get_page48_service),
):
    await service.delete_post(postId, current_user.userId, is_admin=False)
    return {"message": "Post deleted successfully"}


@router.post("/posts/{postId}/like", response_model=ToggleResponse)
async def toggle_like(
    postId: str = Path(...),
    current_user: UserCurrent = Depends(get_current_user),
    _: bool = Depends(require_csrf_protection),
    service: Page48Service = Depends(get_page48_service),
):
    return await service.toggle_like(postId, current_user.userId)


@router.post("/posts/{postId}/repost", response_model=ToggleResponse)
async def toggle_repost(
    postId: str = Path(...),
    current_user: UserCurrent = Depends(get_current_user),
    _: bool = Depends(require_csrf_protection),
    service: Page48Service = Depends(get_page48_service),
):
    return await service.toggle_repost(postId, current_user.userId)


@router.post("/posts/{postId}/bookmark", response_model=ToggleResponse)
async def toggle_bookmark(
    postId: str = Path(...),
    current_user: UserCurrent = Depends(get_current_user),
    _: bool = Depends(require_csrf_protection),
    service: Page48Service = Depends(get_page48_service),
):
    return await service.toggle_bookmark(postId, current_user.userId)


@router.get("/me/bookmarks", response_model=PostPaginationResponse)
async def get_my_bookmarks(
    limit: int = Query(20, le=50),
    cursor: Optional[str] = None,
    current_user: UserCurrent = Depends(get_current_user),
    service: Page48Service = Depends(get_page48_service),
):
    return await service.get_user_bookmarks(current_user.userId, limit, cursor)


@router.get("/me/likes", response_model=PostPaginationResponse)
async def get_my_likes(
    limit: int = Query(20, le=50),
    cursor: Optional[str] = None,
    current_user: UserCurrent = Depends(get_current_user),
    service: Page48Service = Depends(get_page48_service),
):
    return await service.get_user_likes(current_user.userId, limit, cursor)


# Admin
@router.delete("/admin/posts/{postId}")
async def admin_delete_post(
    postId: str = Path(...),
    current_user: UserCurrent = Depends(require_admin),
    _: bool = Depends(require_csrf_protection),
    service: Page48Service = Depends(get_page48_service),
):
    await service.delete_post(postId, current_user.userId, is_admin=True)
    return {"message": "Post deleted by admin"}
