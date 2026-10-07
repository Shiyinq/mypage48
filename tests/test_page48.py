"""End-to-end API tests for the Page48 social module.

Every test drives the real HTTP surface (`/api/page48/...`) through the shared
`client` fixture, so router, dependencies, schemas and service are exercised
together. External storage (MinIO/R2) is mocked with a fake StorageService, so
these tests never need a running object store.

Layout mirrors the endpoint groups in `src/page48/route.py`:
  feed / posts (read) / users (read) / write / social / privacy / search /
  notifications / admin.
"""

import asyncio
import base64
import io
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.dependencies import get_storage_service
from src.main import app
from src.storage.service import StorageService

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

_VALID_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQG"
    "AhKmMIQAAAABJRU5ErkJggg=="
)


class _MockStorageRepository:
    """Minimal stand-in for StorageRepository, mirroring tests/test_storage.py."""

    def __init__(self):
        self.upload_file = AsyncMock()
        self.get_presigned_url = AsyncMock(
            return_value="https://cdn.example.com/object.mp4"
        )
        self.file_exists = AsyncMock(return_value=True)
        self.delete_file = AsyncMock(return_value=True)
        self.check_connection = AsyncMock(return_value=True)
        self.get_file_with_metadata = AsyncMock(
            return_value=(_VALID_PNG_BYTES, "image/png")
        )
        self.get_file_stream_with_metadata = AsyncMock(
            return_value=(io.BytesIO(_VALID_PNG_BYTES), "image/png")
        )
        self.get_metadata = AsyncMock(
            return_value={"blurhash": "U2TI:j|cfQ|c|cjtfQjtfQfQfQfQ|cjtfQjt"}
        )


@pytest.fixture
def storage_service():
    """Override the app's StorageService with one backed by a mock repository.

    Both `/storage/upload` and `/page48/videos` (and the video-ref validation in
    `POST /posts`) resolve `get_storage_service`, so overriding it once covers
    every storage touchpoint in these tests.
    """
    repo = _MockStorageRepository()
    settings = MagicMock()
    settings.MINIO_BUCKET = "test-bucket"
    settings.secret_key = "test-secret-key-for-hmac-signing-purposes"
    settings.algorithm = "HS256"
    settings.api_base_url = "http://localhost:8080/api"
    settings.storage_use_presigned = False
    service = StorageService(repository=repo, config=settings)

    app.dependency_overrides[get_storage_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(get_storage_service, None)


@pytest.fixture
def make_post(client):
    """Create a Page48 post through the API and return its JSON body."""

    async def _make(headers, content="hello world", **overrides):
        payload = {"content": content}
        payload.update(overrides)
        res = await client.post("/api/page48/posts", json=payload, headers=headers)
        assert res.status_code == 201, res.text
        return res.json()

    return _make


@pytest.fixture
def make_thread(client):
    """Publish a Page48 thread (>= 2 items) and return its JSON body."""

    async def _make(headers, contents):
        body = {"posts": [{"content": c} for c in contents]}
        res = await client.post("/api/page48/posts/thread", json=body, headers=headers)
        assert res.status_code == 201, res.text
        return res.json()

    return _make


@pytest.fixture
def follow(client):
    async def _follow(headers, username):
        res = await client.post(f"/api/page48/users/{username}/follow", headers=headers)
        assert res.status_code == 200, res.text
        return res.json()

    return _follow


async def _wait_for_notifications(client, headers, tab, expected, attempts=40):
    """Post-creation notifications are fire-and-forget (`asyncio.create_task`),
    so poll briefly until they land instead of asserting immediately."""
    body = {"data": []}
    for _ in range(attempts):
        res = await client.get(f"/api/page48/notifications?tab={tab}", headers=headers)
        body = res.json()
        if len(body["data"]) >= expected:
            return body
        await asyncio.sleep(0.05)
    return body


# --------------------------------------------------------------------------- #
# Feed
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_feed_public_returns_posts(client, create_user, make_post):
    _, _, headers = await create_user("p48_feed_a")
    await make_post(headers, "feed hello one")
    await make_post(headers, "feed hello two")

    res = await client.get("/api/page48/feed")
    assert res.status_code == 200
    body = res.json()
    assert len(body["data"]) == 2
    assert body["meta"]["hasMore"] is False


@pytest.mark.asyncio
async def test_feed_limit_out_of_range(client):
    res = await client.get("/api/page48/feed?limit=51")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_feed_invalid_media_filter(client):
    res = await client.get("/api/page48/feed?media=audio")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_feed_media_filter_selects_only_images(client, create_user, make_post):
    _, user_id, headers = await create_user("p48_feed_media")
    await make_post(headers, "just text here")
    await make_post(
        headers,
        "a picture",
        images=[{"filename": f"page48/{user_id}/pic.webp", "width": 4, "height": 3}],
    )

    images = (await client.get("/api/page48/feed?media=image")).json()["data"]
    assert len(images) == 1
    assert images[0]["images"]

    texts = (await client.get("/api/page48/feed?media=text")).json()["data"]
    assert len(texts) == 1
    assert texts[0]["images"] == []


@pytest.mark.asyncio
async def test_feed_following_requires_login(client):
    res = await client.get("/api/page48/feed?following=true")
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_feed_following_only_returns_followed_accounts(
    client, create_user, make_post, follow
):
    _, _, alice = await create_user("p48_follow_a")
    _, _, bob = await create_user("p48_follow_b")
    await make_post(bob, "bob post")
    await follow(alice, "p48_follow_b")

    res = await client.get("/api/page48/feed?following=true", headers=alice)
    assert res.status_code == 200
    contents = [p["content"] for p in res.json()["data"]]
    assert "bob post" in contents


@pytest.mark.asyncio
async def test_feed_cursor_pagination(client, create_user, make_post):
    _, _, headers = await create_user("p48_feed_page")
    for index in range(3):
        await make_post(headers, f"page post {index}")

    first = (await client.get("/api/page48/feed?limit=2")).json()
    assert len(first["data"]) == 2
    assert first["meta"]["hasMore"] is True
    assert first["meta"]["nextCursor"]

    second = (
        await client.get(
            f"/api/page48/feed?limit=2&cursor={first['meta']['nextCursor']}"
        )
    ).json()
    assert len(second["data"]) == 1
    ids = {p["postId"] for p in first["data"]} | {p["postId"] for p in second["data"]}
    assert len(ids) == 3


# --------------------------------------------------------------------------- #
# Post read: detail, thread, replies, activity, quotes, reposts, likes
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_get_post_detail(client, create_user, make_post):
    _, user_id, headers = await create_user("p48_post_detail")
    post = await make_post(headers, "detail me")

    res = await client.get(f"/api/page48/posts/{post['postId']}")
    assert res.status_code == 200
    body = res.json()
    assert body["postId"] == post["postId"]
    assert body["content"] == "detail me"
    assert body["userId"] == user_id
    assert body["images"] == []
    assert body["isLiked"] is False


@pytest.mark.asyncio
async def test_get_post_not_found(client):
    res = await client.get("/api/page48/posts/does-not-exist")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_thread_and_direct_replies(client, create_user, make_post):
    _, _, author = await create_user("p48_thread_author")
    root = await make_post(author, "thread root")

    _, _, replier = await create_user("p48_thread_replier")
    reply = await make_post(replier, "a reply", parentPostId=root["postId"])

    thread = (await client.get(f"/api/page48/posts/{root['postId']}/thread")).json()
    assert thread["post"]["postId"] == root["postId"]
    assert thread["replies"][0]["post"]["postId"] == reply["postId"]

    replies = (await client.get(f"/api/page48/posts/{root['postId']}/replies")).json()
    assert [p["postId"] for p in replies["data"]] == [reply["postId"]]


@pytest.mark.asyncio
async def test_post_activity_author_can_view_likes(client, create_user, make_post):
    _, _, author = await create_user("p48_act_author")
    post = await make_post(author, "activity post")

    as_author = (
        await client.get(f"/api/page48/posts/{post['postId']}/activity", headers=author)
    ).json()
    assert as_author["canViewLikes"] is True
    assert as_author["post"]["postId"] == post["postId"]

    as_guest = (await client.get(f"/api/page48/posts/{post['postId']}/activity")).json()
    assert as_guest["canViewLikes"] is False


@pytest.mark.asyncio
async def test_post_quotes(client, create_user, make_post):
    _, _, author = await create_user("p48_quote_author")
    original = await make_post(author, "original post")

    _, _, quoter = await create_user("p48_quoter")
    await make_post(quoter, "my quote", quotedPostId=original["postId"])

    res = await client.get(f"/api/page48/posts/{original['postId']}/quotes")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1


@pytest.mark.asyncio
async def test_post_likes_author_only(client, create_user, make_post):
    _, _, author = await create_user("p48_likes_author")
    post = await make_post(author, "like me")

    # Guest cannot read the list at all.
    assert (
        await client.get(f"/api/page48/posts/{post['postId']}/likes")
    ).status_code == 401

    # A different signed-in user is refused.
    _, _, other = await create_user("p48_likes_other")
    assert (
        await client.get(f"/api/page48/posts/{post['postId']}/likes", headers=other)
    ).status_code == 403

    # The author can.
    res = await client.get(f"/api/page48/posts/{post['postId']}/likes", headers=author)
    assert res.status_code == 200
    assert res.json()["data"] == []


# --------------------------------------------------------------------------- #
# User read: posts / replies / profile / reposts, tags, active users
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_user_posts_and_reposts(client, create_user, make_post):
    _, _, author = await create_user("p48_u_posts")
    await make_post(author, "user post one")

    res = await client.get("/api/page48/users/p48_u_posts/posts")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1

    reposts = await client.get("/api/page48/users/p48_u_posts/reposts")
    assert reposts.status_code == 200
    assert reposts.json()["data"] == []


@pytest.mark.asyncio
async def test_user_posts_media_filter(client, create_user, make_post):
    _, user_id, headers = await create_user("p48_u_media")
    await make_post(headers, "text only")
    await make_post(
        headers,
        "with pic",
        images=[{"filename": f"page48/{user_id}/x.webp", "width": 2, "height": 2}],
    )

    images = (
        await client.get("/api/page48/users/p48_u_media/posts?media=image")
    ).json()["data"]
    assert len(images) == 1

    texts = (await client.get("/api/page48/users/p48_u_media/posts?media=text")).json()[
        "data"
    ]
    assert len(texts) == 1


@pytest.mark.asyncio
async def test_user_replies(client, create_user, make_post):
    _, _, author = await create_user("p48_u_reply_author")
    root = await make_post(author, "root")

    _, _, replier = await create_user("p48_u_replier")
    await make_post(replier, "my reply", parentPostId=root["postId"])

    res = await client.get("/api/page48/users/p48_u_replier/replies")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1


@pytest.mark.asyncio
async def test_user_profile(client, create_user):
    _, user_id, _ = await create_user("p48_profile_user", full_name="Profile Person")

    res = await client.get("/api/page48/users/p48_profile_user/profile")
    assert res.status_code == 200
    body = res.json()
    assert body["username"] == "p48_profile_user"
    assert body["name"] == "Profile Person"
    assert body["userId"] == user_id
    assert body["followerCount"] == 0
    assert body["isFollowing"] is False


@pytest.mark.asyncio
async def test_user_profile_not_found(client):
    res = await client.get("/api/page48/users/nobody_here_48/profile")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_trending_tags(client, create_user, make_post):
    _, _, headers = await create_user("p48_trend")
    await make_post(headers, "hello #p48trending world")

    res = await client.get("/api/page48/tags/trending")
    assert res.status_code == 200
    tags = {t["tag"] for t in res.json()["tags"]}
    assert "p48trending" in tags


@pytest.mark.asyncio
async def test_active_users(client, create_user, make_post):
    _, user_id, headers = await create_user("p48_active_user")
    await make_post(headers, "activity")

    res = await client.get("/api/page48/users/active")
    assert res.status_code == 200
    ids = {u["userId"] for u in res.json()["users"]}
    assert user_id in ids


@pytest.mark.asyncio
async def test_active_users_limit_validation(client):
    assert (await client.get("/api/page48/users/active?limit=21")).status_code == 422


@pytest.mark.asyncio
async def test_posts_by_tag(client, create_user, make_post):
    _, _, headers = await create_user("p48_tag_user")
    await make_post(headers, "talking #p48tagtest now")

    res = await client.get("/api/page48/tags/p48tagtest/posts")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1


# --------------------------------------------------------------------------- #
# Write: create / thread / video / edit / delete / pin / private
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_create_post_requires_login(client):
    res = await client.post("/api/page48/posts", json={"content": "nope"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_create_post_validation(client, create_user):
    _, _, headers = await create_user("p48_create_validation")

    # `content` is required (though an empty string is allowed by the schema).
    assert (
        await client.post("/api/page48/posts", json={}, headers=headers)
    ).status_code == 422
    assert (
        await client.post(
            "/api/page48/posts", json={"content": "a" * 501}, headers=headers
        )
    ).status_code == 422
    assert (
        await client.post(
            "/api/page48/posts",
            json={
                "content": "too many",
                "images": [{"filename": f"page48/x/{i}.webp"} for i in range(11)],
            },
            headers=headers,
        )
    ).status_code == 422


@pytest.mark.asyncio
async def test_create_post_image_and_video_conflict(client, create_user):
    _, user_id, headers = await create_user("p48_media_conflict")
    payload = {
        "content": "mixed media",
        "images": [{"filename": f"page48/{user_id}/a.webp"}],
        "videos": [{"filename": f"page48/{user_id}/a.mp4"}],
    }
    res = await client.post("/api/page48/posts", json=payload, headers=headers)
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_create_reply_parent_not_found(client, create_user):
    _, _, headers = await create_user("p48_bad_parent")
    res = await client.post(
        "/api/page48/posts",
        json={"content": "orphan", "parentPostId": "missing-id"},
        headers=headers,
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_create_quote_not_found(client, create_user):
    _, _, headers = await create_user("p48_bad_quote")
    res = await client.post(
        "/api/page48/posts",
        json={"content": "quote", "quotedPostId": "missing-id"},
        headers=headers,
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_create_post_poll_rules(client, create_user):
    _, user_id, headers = await create_user("p48_poll_rules")

    too_few = await client.post(
        "/api/page48/posts",
        json={"content": "poll", "poll": {"options": ["only one"]}},
        headers=headers,
    )
    assert too_few.status_code == 400

    too_many = await client.post(
        "/api/page48/posts",
        json={"content": "poll", "poll": {"options": [f"o{i}" for i in range(7)]}},
        headers=headers,
    )
    assert too_many.status_code == 400

    with_media = await client.post(
        "/api/page48/posts",
        json={
            "content": "poll with image",
            "poll": {"options": ["a", "b"]},
            "images": [{"filename": f"page48/{user_id}/y.webp"}],
        },
        headers=headers,
    )
    assert with_media.status_code == 400


@pytest.mark.asyncio
async def test_create_poll_and_vote(client, create_user):
    _, _, author = await create_user("p48_poll_author")
    post = await client.post(
        "/api/page48/posts",
        json={"content": "best option?", "poll": {"options": ["one", "two"]}},
        headers=author,
    )
    assert post.status_code == 201
    poll = post.json()["poll"]
    assert poll["totalVotes"] == 0
    assert poll["isExpired"] is False
    option_id = poll["options"][0]["id"]

    _, _, voter = await create_user("p48_poll_voter")
    voted = await client.post(
        f"/api/page48/posts/{post.json()['postId']}/poll/vote",
        json={"optionId": option_id},
        headers=voter,
    )
    assert voted.status_code == 200
    assert voted.json()["myOptionId"] == option_id
    assert voted.json()["totalVotes"] == 1

    # Voting twice is refused.
    again = await client.post(
        f"/api/page48/posts/{post.json()['postId']}/poll/vote",
        json={"optionId": option_id},
        headers=voter,
    )
    assert again.status_code == 400

    # An unknown option is refused.
    invalid = await client.post(
        f"/api/page48/posts/{post.json()['postId']}/poll/vote",
        json={"optionId": "nope"},
        headers=voter,
    )
    assert invalid.status_code == 400


@pytest.mark.asyncio
async def test_vote_poll_without_poll(client, create_user, make_post):
    _, _, headers = await create_user("p48_poll_none")
    post = await make_post(headers, "no poll here")
    res = await client.post(
        f"/api/page48/posts/{post['postId']}/poll/vote",
        json={"optionId": "x"},
        headers=headers,
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_create_thread(client, create_user):
    _, _, headers = await create_user("p48_thread_maker")

    too_short = await client.post(
        "/api/page48/posts/thread",
        json={"posts": [{"content": "lonely"}]},
        headers=headers,
    )
    assert too_short.status_code == 400

    res = await client.post(
        "/api/page48/posts/thread",
        json={"posts": [{"content": "one"}, {"content": "two"}, {"content": "three"}]},
        headers=headers,
    )
    assert res.status_code == 201
    body = res.json()
    assert len(body["posts"]) == 3
    assert body["posts"][1]["parentPostId"] == body["posts"][0]["postId"]


@pytest.mark.asyncio
async def test_upload_video_success(client, create_user, storage_service):
    _, _, headers = await create_user("p48_video_uploader")
    res = await client.post(
        "/api/page48/videos",
        files={"file": ("clip.mp4", b"binary-video-bytes", "video/mp4")},
        data={"width": "1080", "height": "1920", "duration": "5.5"},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["filename"].startswith("page48/")
    assert body["filename"].endswith(".mp4")
    assert body["url"]


@pytest.mark.asyncio
async def test_upload_video_invalid_type(client, create_user, storage_service):
    _, _, headers = await create_user("p48_video_badtype")
    res = await client.post(
        "/api/page48/videos",
        files={"file": ("clip.txt", b"not a video", "text/plain")},
        headers=headers,
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_upload_video_empty(client, create_user, storage_service):
    _, _, headers = await create_user("p48_video_empty")
    res = await client.post(
        "/api/page48/videos",
        files={"file": ("clip.mp4", b"", "video/mp4")},
        headers=headers,
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_upload_video_too_large(
    client, create_user, storage_service, monkeypatch
):
    from src.config import config

    monkeypatch.setattr(config, "MAX_PAGE48_VIDEO_UPLOAD_SIZE_BYTES", 4)
    _, _, headers = await create_user("p48_video_big")
    res = await client.post(
        "/api/page48/videos",
        files={"file": ("clip.mp4", b"12345", "video/mp4")},
        headers=headers,
    )
    assert res.status_code == 413


@pytest.mark.asyncio
async def test_create_post_with_video_reference(client, create_user, storage_service):
    _, user_id, headers = await create_user("p48_video_ref")

    ok = await client.post(
        "/api/page48/posts",
        json={
            "content": "with video",
            "videos": [
                {
                    "filename": f"page48/{user_id}/clip.mp4",
                    "width": 1080,
                    "height": 1920,
                    "duration": 5.0,
                }
            ],
        },
        headers=headers,
    )
    assert ok.status_code == 201, ok.text
    assert len(ok.json()["videos"]) == 1

    # A reference that lives under somebody else's prefix is rejected.
    foreign = await client.post(
        "/api/page48/posts",
        json={
            "content": "stolen video",
            "videos": [{"filename": "page48/someone-else/clip.mp4"}],
        },
        headers=headers,
    )
    assert foreign.status_code == 400

    # A reference that does not exist in storage is rejected.
    storage_service.repository.file_exists.return_value = False
    missing = await client.post(
        "/api/page48/posts",
        json={
            "content": "ghost video",
            "videos": [{"filename": f"page48/{user_id}/ghost.mp4"}],
        },
        headers=headers,
    )
    assert missing.status_code == 400


@pytest.mark.asyncio
async def test_storage_image_upload_then_post(client, create_user, storage_service):
    """Smoke test: the real image-upload path feeds a new Page48 post."""
    _, _, headers = await create_user("p48_image_smoke")
    upload = await client.post(
        "/api/storage/upload",
        json={
            "image": "data:image/png;base64,"
            + base64.b64encode(_VALID_PNG_BYTES).decode(),
            "category": "page48",
        },
        headers=headers,
    )
    assert upload.status_code == 201, upload.text
    filename = upload.json()["filename"]
    assert filename.startswith("page48/")

    post = await client.post(
        "/api/page48/posts",
        json={
            "content": "look at this",
            "images": [{"filename": filename, "width": 1, "height": 1}],
        },
        headers=headers,
    )
    assert post.status_code == 201, post.text
    assert post.json()["images"][0]["filename"] == filename


@pytest.mark.asyncio
async def test_edit_post(client, create_user, make_post):
    _, _, author = await create_user("p48_edit_author")
    post = await make_post(author, "before edit")

    edited = await client.patch(
        f"/api/page48/posts/{post['postId']}",
        json={"content": "after edit"},
        headers=author,
    )
    assert edited.status_code == 200
    assert edited.json()["content"] == "after edit"
    assert edited.json()["isEdited"] is True

    # A stranger cannot edit it.
    _, _, other = await create_user("p48_edit_other")
    denied = await client.patch(
        f"/api/page48/posts/{post['postId']}",
        json={"content": "hijacked"},
        headers=other,
    )
    assert denied.status_code == 403

    # A missing post is a 404.
    missing = await client.patch(
        "/api/page48/posts/missing-id",
        json={"content": "x"},
        headers=author,
    )
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_delete_post(client, create_user, make_post):
    _, _, author = await create_user("p48_delete_author")
    post = await make_post(author, "delete me")

    _, _, other = await create_user("p48_delete_other")
    denied = await client.delete(f"/api/page48/posts/{post['postId']}", headers=other)
    assert denied.status_code == 403

    ok = await client.delete(f"/api/page48/posts/{post['postId']}", headers=author)
    assert ok.status_code == 200
    assert (await client.get(f"/api/page48/posts/{post['postId']}")).status_code == 404


@pytest.mark.asyncio
async def test_pin_and_unpin_post(client, create_user, make_post):
    _, _, author = await create_user("p48_pin_author")
    post = await make_post(author, "pin me")

    pinned = await client.post(
        f"/api/page48/posts/{post['postId']}/pin", headers=author
    )
    assert pinned.status_code == 200
    assert pinned.json()["isPinned"] is True

    unpinned = await client.delete(
        f"/api/page48/posts/{post['postId']}/pin", headers=author
    )
    assert unpinned.status_code == 200
    assert unpinned.json()["isPinned"] is False


@pytest.mark.asyncio
async def test_pin_rules(client, create_user, make_post):
    _, _, author = await create_user("p48_pin_rules_author")
    root = await make_post(author, "root")

    _, _, replier = await create_user("p48_pin_rules_replier")
    reply = await make_post(replier, "a reply", parentPostId=root["postId"])

    cannot_pin_reply = await client.post(
        f"/api/page48/posts/{reply['postId']}/pin", headers=replier
    )
    assert cannot_pin_reply.status_code == 400

    not_owner = await client.post(
        f"/api/page48/posts/{root['postId']}/pin", headers=replier
    )
    assert not_owner.status_code == 403


@pytest.mark.asyncio
async def test_private_post_visibility(client, create_user, make_post):
    _, _, author = await create_user("p48_private_author")
    post = await make_post(author, "secret plans")

    made_private = await client.post(
        f"/api/page48/posts/{post['postId']}/private", headers=author
    )
    assert made_private.status_code == 200
    assert made_private.json()["isPrivate"] is True

    # The author keeps it; everyone else gets a 404.
    assert (
        await client.get(f"/api/page48/posts/{post['postId']}", headers=author)
    ).status_code == 200
    assert (await client.get(f"/api/page48/posts/{post['postId']}")).status_code == 404

    made_public = await client.delete(
        f"/api/page48/posts/{post['postId']}/private", headers=author
    )
    assert made_public.status_code == 200
    assert made_public.json()["isPrivate"] is False
    assert (await client.get(f"/api/page48/posts/{post['postId']}")).status_code == 200


@pytest.mark.asyncio
async def test_private_reply_not_allowed(client, create_user, make_post):
    _, _, author = await create_user("p48_priv_reply_author")
    root = await make_post(author, "root")

    _, _, replier = await create_user("p48_priv_reply_replier")
    reply = await make_post(replier, "a reply", parentPostId=root["postId"])

    res = await client.post(
        f"/api/page48/posts/{reply['postId']}/private", headers=replier
    )
    assert res.status_code == 400


# --------------------------------------------------------------------------- #
# Social: like / repost / bookmark / report / follows
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_toggle_like(client, create_user, make_post):
    _, _, author = await create_user("p48_like_author")
    post = await make_post(author, "like target")

    _, _, liker = await create_user("p48_liker")
    on = await client.post(f"/api/page48/posts/{post['postId']}/like", headers=liker)
    assert on.status_code == 200
    assert on.json() == {"status": True, "count": 1}

    off = await client.post(f"/api/page48/posts/{post['postId']}/like", headers=liker)
    assert off.json() == {"status": False, "count": 0}

    assert (
        await client.post("/api/page48/posts/missing/like", headers=liker)
    ).status_code == 404


@pytest.mark.asyncio
async def test_toggle_repost_and_bookmark(client, create_user, make_post):
    _, _, author = await create_user("p48_repost_author")
    post = await make_post(author, "repost target")

    _, _, actor = await create_user("p48_reposter")
    repost = await client.post(
        f"/api/page48/posts/{post['postId']}/repost", headers=actor
    )
    assert repost.json() == {"status": True, "count": 1}

    bookmark = await client.post(
        f"/api/page48/posts/{post['postId']}/bookmark", headers=actor
    )
    assert bookmark.json() == {"status": True, "count": 1}
    assert (await client.get(f"/api/page48/posts/{post['postId']}/reposts")).json()[
        "data"
    ][0]["username"] == "p48_reposter"


@pytest.mark.asyncio
async def test_my_bookmarks_and_likes(client, create_user, make_post):
    _, _, author = await create_user("p48_me_author")
    post = await make_post(author, "save me")

    _, _, actor = await create_user("p48_me_actor")
    await client.post(f"/api/page48/posts/{post['postId']}/like", headers=actor)
    await client.post(f"/api/page48/posts/{post['postId']}/bookmark", headers=actor)

    bookmarks = await client.get("/api/page48/me/bookmarks", headers=actor)
    assert bookmarks.status_code == 200
    assert [p["postId"] for p in bookmarks.json()["data"]] == [post["postId"]]

    likes = await client.get("/api/page48/me/likes", headers=actor)
    assert [p["postId"] for p in likes.json()["data"]] == [post["postId"]]

    # Both lists are private.
    assert (await client.get("/api/page48/me/bookmarks")).status_code == 401


@pytest.mark.asyncio
async def test_create_report(client, create_user, make_post):
    _, _, author = await create_user("p48_report_author")
    post = await make_post(author, "reportable")

    _, _, reporter = await create_user("p48_reporter")
    created = await client.post(
        "/api/page48/reports",
        json={"targetType": "post", "targetId": post["postId"], "reason": "spam"},
        headers=reporter,
    )
    assert created.status_code == 201
    assert created.json()["status"] == "pending"

    # Reporting the same target twice is refused.
    duplicate = await client.post(
        "/api/page48/reports",
        json={"targetType": "post", "targetId": post["postId"], "reason": "spam"},
        headers=reporter,
    )
    assert duplicate.status_code == 400

    # Reporting yourself is refused.
    self_report = await client.post(
        "/api/page48/reports",
        json={"targetType": "user", "targetId": post["userId"], "reason": "other"},
        headers=author,
    )
    assert self_report.status_code == 400

    # A missing target is refused.
    missing = await client.post(
        "/api/page48/reports",
        json={"targetType": "user", "targetId": "who", "reason": "other"},
        headers=reporter,
    )
    assert missing.status_code == 400

    # Reporting requires login.
    assert (
        await client.post(
            "/api/page48/reports",
            json={"targetType": "user", "targetId": "who", "reason": "other"},
        )
    ).status_code == 401


@pytest.mark.asyncio
async def test_follow_and_unfollow(client, create_user, follow):
    _, _, alice = await create_user("p48_f_alice")
    _, _, bob = await create_user("p48_f_bob")

    result = await follow(alice, "p48_f_bob")
    assert result["isFollowing"] is True
    assert result["followerCount"] == 1

    profile = (
        await client.get("/api/page48/users/p48_f_bob/profile", headers=alice)
    ).json()
    assert profile["isFollowing"] is True

    unfollowed = await client.delete(
        "/api/page48/users/p48_f_bob/follow", headers=alice
    )
    assert unfollowed.json()["isFollowing"] is False

    # Following yourself is refused.
    assert (
        await client.post("/api/page48/users/p48_f_alice/follow", headers=alice)
    ).status_code == 400

    # Following requires login.
    assert (await client.post("/api/page48/users/p48_f_bob/follow")).status_code == 401


@pytest.mark.asyncio
async def test_follower_and_following_lists_require_login(client, create_user, follow):
    _, _, alice = await create_user("p48_fl_alice")
    _, _, bob = await create_user("p48_fl_bob")
    await follow(alice, "p48_fl_bob")

    assert (
        await client.get("/api/page48/users/p48_fl_bob/followers")
    ).status_code == 401

    followers = (
        await client.get("/api/page48/users/p48_fl_bob/followers", headers=bob)
    ).json()
    assert [u["username"] for u in followers["data"]] == ["p48_fl_alice"]

    following = (
        await client.get("/api/page48/users/p48_fl_alice/following", headers=alice)
    ).json()
    assert [u["username"] for u in following["data"]] == ["p48_fl_bob"]


# --------------------------------------------------------------------------- #
# Privacy: block / mute / locked account
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_block_hides_and_severs(client, create_user, make_post, follow):
    _, _, alice = await create_user("p48_b_alice")
    _, _, bob = await create_user("p48_b_bob")
    bob_post = await make_post(bob, "bob public post")
    await follow(alice, "p48_b_bob")

    blocked = await client.post("/api/page48/users/p48_b_bob/block", headers=alice)
    assert blocked.status_code == 200
    assert blocked.json()["isBlocked"] is True

    # Blocking severs the follow both ways.
    following = (
        await client.get("/api/page48/users/p48_b_alice/following", headers=alice)
    ).json()
    assert following["data"] == []

    # Bob's post disappears from Alice's feed and is a 404 on direct access.
    feed = (await client.get("/api/page48/feed", headers=alice)).json()["data"]
    assert bob_post["postId"] not in [p["postId"] for p in feed]
    assert (
        await client.get(f"/api/page48/posts/{bob_post['postId']}", headers=alice)
    ).status_code == 404

    # Following through a block is refused.
    assert (
        await client.post("/api/page48/users/p48_b_bob/follow", headers=alice)
    ).status_code == 403

    # Bob sees the block from his side too.
    profile = (
        await client.get("/api/page48/users/p48_b_alice/profile", headers=bob)
    ).json()
    assert profile["isBlockedBy"] is True

    unblocked = await client.delete("/api/page48/users/p48_b_bob/block", headers=alice)
    assert unblocked.json()["isBlocked"] is False
    assert (
        await client.get(f"/api/page48/posts/{bob_post['postId']}", headers=alice)
    ).status_code == 200


@pytest.mark.asyncio
async def test_block_self_forbidden(client, create_user):
    _, _, alice = await create_user("p48_b_self")
    assert (
        await client.post("/api/page48/users/p48_b_self/block", headers=alice)
    ).status_code == 400


@pytest.mark.asyncio
async def test_mute_hides_from_feed_only(client, create_user, make_post):
    _, _, alice = await create_user("p48_m_alice")
    _, _, bob = await create_user("p48_m_bob")
    await make_post(bob, "bob unique zebra post")

    muted = await client.post("/api/page48/users/p48_m_bob/mute", headers=alice)
    assert muted.status_code == 200
    assert muted.json()["isMuted"] is True

    # Hidden from the timeline...
    feed = (await client.get("/api/page48/feed", headers=alice)).json()["data"]
    assert feed == []
    # ...but still reachable by search and by profile.
    search = (
        await client.get("/api/page48/search/posts?query=zebra", headers=alice)
    ).json()
    assert len(search["data"]) == 1
    profile_posts = (
        await client.get("/api/page48/users/p48_m_bob/posts", headers=alice)
    ).json()
    assert len(profile_posts["data"]) == 1

    blocks = await client.get("/api/page48/me/blocks", headers=alice)
    mutes = await client.get("/api/page48/me/mutes", headers=alice)
    assert blocks.json()["data"] == []
    assert [u["username"] for u in mutes.json()["data"]] == ["p48_m_bob"]

    # Unmuting brings the posts back into the timeline.
    unmuted = await client.delete("/api/page48/users/p48_m_bob/mute", headers=alice)
    assert unmuted.status_code == 200
    assert unmuted.json()["isMuted"] is False
    feed_again = (await client.get("/api/page48/feed", headers=alice)).json()["data"]
    assert len(feed_again) == 1


@pytest.mark.asyncio
async def test_mute_self_forbidden(client, create_user):
    _, _, alice = await create_user("p48_m_self")
    assert (
        await client.post("/api/page48/users/p48_m_self/mute", headers=alice)
    ).status_code == 400


@pytest.mark.asyncio
async def test_locked_account_requires_approved_followers(
    client, create_user, make_post, follow
):
    _, _, owner = await create_user("p48_lock_owner")
    _, _, fan = await create_user("p48_lock_fan")
    _, _, stranger = await create_user("p48_lock_stranger")

    locked = await client.patch(
        "/api/page48/me/settings", json={"locked": True}, headers=owner
    )
    assert locked.status_code == 200
    assert locked.json()["locked"] is True

    post = await make_post(owner, "followers only")

    # A stranger (and a guest) cannot read it.
    assert (
        await client.get(f"/api/page48/posts/{post['postId']}", headers=stranger)
    ).status_code == 404
    assert (await client.get(f"/api/page48/posts/{post['postId']}")).status_code == 404

    # Following a locked account creates a pending request.
    request = await follow(fan, "p48_lock_owner")
    assert request["isPending"] is True
    assert request["isFollowing"] is False
    assert (
        await client.get(f"/api/page48/posts/{post['postId']}", headers=fan)
    ).status_code == 404

    # The owner approves, and only then does the post become visible.
    accepted = await client.post(
        "/api/page48/users/p48_lock_fan/follow/accept", headers=owner
    )
    assert accepted.status_code == 200
    assert (
        await client.get(f"/api/page48/posts/{post['postId']}", headers=fan)
    ).status_code == 200


@pytest.mark.asyncio
async def test_decline_follow_request(client, create_user, follow):
    _, _, owner = await create_user("p48_decline_owner")
    _, _, fan = await create_user("p48_decline_fan")

    await client.patch("/api/page48/me/settings", json={"locked": True}, headers=owner)
    await follow(fan, "p48_decline_owner")

    declined = await client.delete(
        "/api/page48/users/p48_decline_fan/follow/request", headers=owner
    )
    assert declined.status_code == 200
    assert declined.json()["isFollowing"] is False

    profile = (
        await client.get("/api/page48/users/p48_decline_owner/profile", headers=fan)
    ).json()
    assert profile["isFollowPending"] is False


# --------------------------------------------------------------------------- #
# Search (signed-in only)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_search_requires_login(client):
    for path in (
        "/api/page48/search/top?query=zebra",
        "/api/page48/search/posts?query=zebra",
        "/api/page48/search/users?query=zebra",
        "/api/page48/search/tags?query=zebra",
    ):
        assert (await client.get(path)).status_code == 401


@pytest.mark.asyncio
async def test_search_posts_by_keyword_and_media(client, create_user, make_post):
    _, user_id, author = await create_user("p48_search_author")
    await make_post(author, "a unique zebra appears")
    await make_post(
        author,
        "zebra with picture",
        images=[{"filename": f"page48/{user_id}/z.webp", "width": 2, "height": 2}],
    )

    _, _, searcher = await create_user("p48_searcher")

    all_hits = await client.get(
        "/api/page48/search/posts?query=zebra", headers=searcher
    )
    assert all_hits.status_code == 200
    assert len(all_hits.json()["data"]) == 2

    media_hits = await client.get(
        "/api/page48/search/posts?query=zebra&tab=media", headers=searcher
    )
    assert len(media_hits.json()["data"]) == 1


@pytest.mark.asyncio
async def test_search_users_and_tags(client, create_user, make_post):
    # Usernames are matched by prefix, so keep the searched word at the start.
    _, _, author = await create_user("findme_p48")
    await make_post(author, "hello #p48findtag")

    _, _, searcher = await create_user("p48_searcher2")

    users = await client.get("/api/page48/search/users?query=findme", headers=searcher)
    assert any(u["username"] == "findme_p48" for u in users.json()["data"])

    tags = await client.get(
        "/api/page48/search/tags?query=p48findtag", headers=searcher
    )
    assert any(t["tag"] == "p48findtag" for t in tags.json()["tags"])

    top = await client.get("/api/page48/search/top?query=findme", headers=searcher)
    assert top.status_code == 200
    assert "users" in top.json() and "tags" in top.json() and "posts" in top.json()


@pytest.mark.asyncio
async def test_search_hides_blocked_authors(client, create_user, make_post):
    _, _, muted_author = await create_user("p48_search_hidden")
    await make_post(muted_author, "searchable zebra")

    _, _, searcher = await create_user("p48_search_blocker")
    await client.post("/api/page48/users/p48_search_hidden/block", headers=searcher)

    res = await client.get("/api/page48/search/posts?query=zebra", headers=searcher)
    assert res.json()["data"] == []


# --------------------------------------------------------------------------- #
# Notifications
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_notifications_empty_and_requires_login(client, create_user):
    _, _, user = await create_user("p48_notif_empty")

    assert (await client.get("/api/page48/notifications")).status_code == 401

    counts = await client.get("/api/page48/notifications/counts", headers=user)
    assert counts.json() == {
        "total": 0,
        "replies": 0,
        "mentions": 0,
        "likes": 0,
        "reposts": 0,
        "follows": 0,
    }

    overview = await client.get("/api/page48/notifications/overview", headers=user)
    assert overview.status_code == 200
    assert overview.json()["total"] == 0


@pytest.mark.asyncio
async def test_like_notification_flow(client, create_user, make_post):
    _, _, author = await create_user("p48_notif_author")
    post = await make_post(author, "notify me")

    _, _, fan = await create_user("p48_notif_fan")
    await client.post(f"/api/page48/posts/{post['postId']}/like", headers=fan)

    counts = (
        await client.get("/api/page48/notifications/counts", headers=author)
    ).json()
    assert counts["likes"] == 1
    assert counts["total"] == 1

    feed = (
        await client.get("/api/page48/notifications?tab=likes", headers=author)
    ).json()
    assert len(feed["data"]) == 1
    assert feed["data"][0]["type"] == "like"
    assert feed["data"][0]["isUnread"] is True
    assert feed["data"][0]["actor"]["username"] == "p48_notif_fan"

    read = await client.post("/api/page48/notifications/read?tab=likes", headers=author)
    assert read.status_code == 200
    assert read.json()["count"] == 1

    after = (
        await client.get("/api/page48/notifications/counts", headers=author)
    ).json()
    assert after["likes"] == 0


@pytest.mark.asyncio
async def test_reply_and_mention_notifications(client, create_user, make_post):
    _, _, author = await create_user("p48_notif_reply_author")
    root = await make_post(author, "root post")

    _, _, replier = await create_user("p48_notif_replier")
    await make_post(replier, "replying now", parentPostId=root["postId"])

    replies = await _wait_for_notifications(client, author, "replies", 1)
    assert len(replies["data"]) == 1

    _, _, mentioned = await create_user("p48_notif_mentioned")
    await make_post(replier, "hey @p48_notif_mentioned hello")

    mentions = await _wait_for_notifications(client, mentioned, "mentions", 1)
    assert len(mentions["data"]) == 1


@pytest.mark.asyncio
async def test_follow_notifications(client, create_user, follow):
    _, _, followed = await create_user("p48_notif_followed")
    _, _, fan = await create_user("p48_notif_follower")
    await follow(fan, "p48_notif_followed")

    follows = (
        await client.get("/api/page48/notifications?tab=follows", headers=followed)
    ).json()
    assert len(follows["data"]) == 1
    assert follows["data"][0]["type"] == "follow"


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_admin_delete_post(client, create_user, make_post):
    _, _, author = await create_user("p48_admin_del_author")
    post = await make_post(author, "to be removed")

    _, _, admin = await create_user("p48_admin_del", is_admin=True)
    deleted = await client.delete(
        f"/api/page48/admin/posts/{post['postId']}", headers=admin
    )
    assert deleted.status_code == 200
    assert (await client.get(f"/api/page48/posts/{post['postId']}")).status_code == 404

    # A normal user (and a guest) cannot reach the admin route.
    _, _, normal = await create_user("p48_admin_del_normal")
    other = await make_post(author, "still here")
    assert (
        await client.delete(
            f"/api/page48/admin/posts/{other['postId']}", headers=normal
        )
    ).status_code == 404
    # Admin routes return 404 (not 401) to hide their existence from guests.
    assert (
        await client.delete(f"/api/page48/admin/posts/{other['postId']}")
    ).status_code == 404


@pytest.mark.asyncio
async def test_admin_reports_list_and_filters(client, create_user, make_post):
    _, _, author = await create_user("p48_admin_rep_author")
    post = await make_post(author, "reported content")

    _, _, reporter = await create_user("p48_admin_rep_reporter")
    await client.post(
        "/api/page48/reports",
        json={"targetType": "post", "targetId": post["postId"], "reason": "spam"},
        headers=reporter,
    )

    _, _, admin = await create_user("p48_admin_rep", is_admin=True)
    listing = await client.get("/api/page48/admin/reports", headers=admin)
    assert listing.status_code == 200
    body = listing.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["targetId"] == post["postId"]
    assert body["data"][0]["targetExists"] is True

    filtered = await client.get(
        "/api/page48/admin/reports?targetType=user", headers=admin
    )
    assert filtered.json()["data"] == []

    invalid = await client.get(
        "/api/page48/admin/reports?targetType=banana", headers=admin
    )
    assert invalid.status_code == 422

    _, _, normal = await create_user("p48_admin_rep_normal")
    assert (
        await client.get("/api/page48/admin/reports", headers=normal)
    ).status_code == 404


# --------------------------------------------------------------------------- #
# Additional use cases (edge branches beyond the happy path)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_poll_expires_after_deadline(client, db, create_user):
    _, _, author = await create_user("p48_poll_exp_author")
    created = await client.post(
        "/api/page48/posts",
        json={"content": "ends soon?", "poll": {"options": ["yes", "no"]}},
        headers=author,
    )
    body = created.json()
    post_id = body["postId"]
    option_id = body["poll"]["options"][0]["id"]

    # Move the deadline into the past, exactly as 24 hours would do.
    await db["page48_posts"].update_one(
        {"postId": post_id},
        {"$set": {"poll.endsAt": datetime.now(timezone.utc) - timedelta(hours=1)}},
    )

    fetched = (await client.get(f"/api/page48/posts/{post_id}", headers=author)).json()
    assert fetched["poll"]["isExpired"] is True

    _, _, voter = await create_user("p48_poll_exp_voter")
    vote = await client.post(
        f"/api/page48/posts/{post_id}/poll/vote",
        json={"optionId": option_id},
        headers=voter,
    )
    assert vote.status_code == 400


@pytest.mark.asyncio
async def test_quote_with_poll_is_rejected(client, create_user, make_post):
    _, _, author = await create_user("p48_qp_author")
    original = await make_post(author, "original")

    _, _, quoter = await create_user("p48_qp_quoter")
    res = await client.post(
        "/api/page48/posts",
        json={
            "content": "quote with poll",
            "quotedPostId": original["postId"],
            "poll": {"options": ["a", "b"]},
        },
        headers=quoter,
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_create_thread_too_long(client, create_user):
    _, _, headers = await create_user("p48_thread_long")
    res = await client.post(
        "/api/page48/posts/thread",
        json={"posts": [{"content": f"part {i}"} for i in range(26)]},
        headers=headers,
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_search_operators(client, create_user, make_post):
    _, _, from_author = await create_user("p48_op_from")
    await make_post(from_author, "operator post")

    _, _, mentioner = await create_user("p48_op_mentioner")
    await make_post(mentioner, "ping @p48_op_target now")

    _, _, tagger = await create_user("p48_op_tagger")
    await make_post(tagger, "hashtag #p48optag here")

    _, _, searcher = await create_user("p48_op_searcher")

    by_author = await client.get(
        "/api/page48/search/posts?query=from:p48_op_from", headers=searcher
    )
    assert [p["content"] for p in by_author.json()["data"]] == ["operator post"]

    by_mention = await client.get(
        "/api/page48/search/posts?query=@p48_op_target", headers=searcher
    )
    assert len(by_mention.json()["data"]) == 1

    by_tag = await client.get(
        "/api/page48/search/posts?query=%23p48optag", headers=searcher
    )
    assert len(by_tag.json()["data"]) == 1


@pytest.mark.asyncio
async def test_quote_includes_preview(client, create_user, make_post):
    _, _, author = await create_user("p48_prev_author")
    original = await make_post(author, "preview me")

    _, _, quoter = await create_user("p48_prev_quoter")
    quote = await make_post(quoter, "quoting", quotedPostId=original["postId"])

    fetched = (await client.get(f"/api/page48/posts/{quote['postId']}")).json()
    assert fetched["quotedPostId"] == original["postId"]
    assert fetched["quotedPost"] is not None
    assert fetched["quotedPost"]["content"] == "preview me"


@pytest.mark.asyncio
async def test_user_reposts_list(client, create_user, make_post):
    _, _, author = await create_user("p48_ur_author")
    post = await make_post(author, "repost target")

    _, _, reposter = await create_user("p48_ur_reposter")
    await client.post(f"/api/page48/posts/{post['postId']}/repost", headers=reposter)

    res = await client.get("/api/page48/users/p48_ur_reposter/reposts")
    data = res.json()["data"]
    assert [p["postId"] for p in data] == [post["postId"]]
    assert data[0]["repostedAt"] is not None


@pytest.mark.asyncio
async def test_cursor_pagination_replies(client, create_user, make_post):
    _, _, author = await create_user("p48_cp_author")
    root = await make_post(author, "root for replies")
    for index in range(3):
        await make_post(author, f"reply {index}", parentPostId=root["postId"])

    first = (
        await client.get(f"/api/page48/posts/{root['postId']}/replies?limit=2")
    ).json()
    assert len(first["data"]) == 2
    assert first["meta"]["hasMore"] is True

    second = (
        await client.get(
            f"/api/page48/posts/{root['postId']}/replies"
            f"?limit=2&cursor={first['meta']['nextCursor']}"
        )
    ).json()
    assert len(second["data"]) == 1
    ids = {p["postId"] for p in first["data"]} | {p["postId"] for p in second["data"]}
    assert len(ids) == 3


@pytest.mark.asyncio
async def test_cursor_pagination_likes(client, create_user, make_post):
    _, _, author = await create_user("p48_cl_author")
    post = await make_post(author, "many likes")

    for name in ("p48_cl_l1", "p48_cl_l2", "p48_cl_l3"):
        _, _, liker = await create_user(name)
        await client.post(f"/api/page48/posts/{post['postId']}/like", headers=liker)

    first = (
        await client.get(
            f"/api/page48/posts/{post['postId']}/likes?limit=2", headers=author
        )
    ).json()
    assert len(first["data"]) == 2
    assert first["meta"]["hasMore"] is True

    second = (
        await client.get(
            f"/api/page48/posts/{post['postId']}/likes"
            f"?limit=2&cursor={first['meta']['nextCursor']}",
            headers=author,
        )
    ).json()
    assert len(second["data"]) == 1


@pytest.mark.asyncio
async def test_cursor_pagination_followers(client, create_user, follow):
    _, _, target = await create_user("p48_cf_target")
    for name in ("p48_cf_1", "p48_cf_2", "p48_cf_3"):
        _, _, follower = await create_user(name)
        await follow(follower, "p48_cf_target")

    first = (
        await client.get(
            "/api/page48/users/p48_cf_target/followers?limit=2", headers=target
        )
    ).json()
    assert len(first["data"]) == 2
    assert first["meta"]["hasMore"] is True

    second = (
        await client.get(
            "/api/page48/users/p48_cf_target/followers"
            f"?limit=2&cursor={first['meta']['nextCursor']}",
            headers=target,
        )
    ).json()
    assert len(second["data"]) == 1


@pytest.mark.asyncio
async def test_locked_reply_hidden_from_thread(client, create_user, make_post, follow):
    _, _, author = await create_user("p48_lr_author")
    root = await make_post(author, "public root")

    _, _, locked = await create_user("p48_lr_locked")
    await client.patch("/api/page48/me/settings", json={"locked": True}, headers=locked)
    await make_post(locked, "locked reply", parentPostId=root["postId"])

    _, _, stranger = await create_user("p48_lr_stranger")
    thread = (
        await client.get(f"/api/page48/posts/{root['postId']}/thread", headers=stranger)
    ).json()
    assert thread["replies"] == []

    # Following a locked account stays a request until the owner approves it.
    await follow(stranger, "p48_lr_locked")
    still_hidden = (
        await client.get(f"/api/page48/posts/{root['postId']}/thread", headers=stranger)
    ).json()
    assert still_hidden["replies"] == []

    await client.post("/api/page48/users/p48_lr_stranger/follow/accept", headers=locked)
    visible = (
        await client.get(f"/api/page48/posts/{root['postId']}/thread", headers=stranger)
    ).json()
    assert len(visible["replies"]) == 1


@pytest.mark.asyncio
async def test_private_reply_inherits_privacy(client, create_user, make_post):
    _, _, author = await create_user("p48_pr_author")
    root = await make_post(author, "private root")
    await client.post(f"/api/page48/posts/{root['postId']}/private", headers=author)

    reply = await make_post(author, "hidden reply", parentPostId=root["postId"])
    assert reply["isPrivate"] is True

    assert (await client.get(f"/api/page48/posts/{reply['postId']}")).status_code == 404
    assert (
        await client.get(f"/api/page48/posts/{reply['postId']}", headers=author)
    ).status_code == 200


@pytest.mark.asyncio
async def test_declining_pending_request_clears_notification(
    client, create_user, follow
):
    _, _, owner = await create_user("p48_up_owner")
    _, _, fan = await create_user("p48_up_fan")

    await client.patch("/api/page48/me/settings", json={"locked": True}, headers=owner)
    await follow(fan, "p48_up_owner")

    before = (
        await client.get("/api/page48/notifications?tab=follows", headers=owner)
    ).json()
    assert len(before["data"]) == 1

    # Cancelling the request has to remove the owner's Follows entry too.
    await client.delete("/api/page48/users/p48_up_owner/follow", headers=fan)

    after = (
        await client.get("/api/page48/notifications?tab=follows", headers=owner)
    ).json()
    assert after["data"] == []


@pytest.mark.asyncio
async def test_accept_without_pending_request(client, create_user):
    _, _, owner = await create_user("p48_ap_owner")
    _, _, other = await create_user("p48_ap_other")

    # Nothing is pending, so this is a no-op: it succeeds but reports that no
    # follow relationship actually exists.
    res = await client.post(
        "/api/page48/users/p48_ap_other/follow/accept", headers=owner
    )
    assert res.status_code == 200
    assert res.json()["isFollowing"] is False


@pytest.mark.asyncio
async def test_accept_pending_request_confirms_follow(client, create_user, follow):
    _, _, owner = await create_user("p48_acc_owner")
    _, _, fan = await create_user("p48_acc_fan")

    await client.patch("/api/page48/me/settings", json={"locked": True}, headers=owner)
    pending = await follow(fan, "p48_acc_owner")
    assert pending["isPending"] is True

    accepted = await client.post(
        "/api/page48/users/p48_acc_fan/follow/accept", headers=owner
    )
    assert accepted.status_code == 200
    assert accepted.json()["isFollowing"] is True

    profile = (
        await client.get("/api/page48/users/p48_acc_owner/profile", headers=fan)
    ).json()
    assert profile["isFollowing"] is True
    assert profile["isFollowPending"] is False


@pytest.mark.asyncio
async def test_block_hides_viewer_from_blocked_account_feed(
    client, create_user, make_post
):
    _, _, alice = await create_user("p48_bw_alice")
    _, _, bob = await create_user("p48_bw_bob")
    alice_post = await make_post(alice, "alice post")
    await make_post(bob, "bob post")

    await client.post("/api/page48/users/p48_bw_bob/block", headers=alice)

    # The block is mutual, so Alice's post is gone from Bob's timeline too.
    bob_feed = (await client.get("/api/page48/feed", headers=bob)).json()["data"]
    assert alice_post["postId"] not in [p["postId"] for p in bob_feed]
    assert (
        await client.get(f"/api/page48/posts/{alice_post['postId']}", headers=bob)
    ).status_code == 404


@pytest.mark.asyncio
async def test_pinned_post_only_on_first_page(client, create_user, make_post):
    _, _, author = await create_user("p48_pin_page")
    posts = [await make_post(author, f"pin page {i}") for i in range(4)]
    pinned = posts[0]
    await client.post(f"/api/page48/posts/{pinned['postId']}/pin", headers=author)

    first = (await client.get("/api/page48/users/p48_pin_page/posts?limit=2")).json()
    assert first["data"][0]["postId"] == pinned["postId"]
    assert first["data"][0]["isPinned"] is True

    second = (
        await client.get(
            "/api/page48/users/p48_pin_page/posts"
            f"?limit=2&cursor={first['meta']['nextCursor']}"
        )
    ).json()
    assert pinned["postId"] not in [p["postId"] for p in second["data"]]

    ids = [p["postId"] for p in first["data"]] + [p["postId"] for p in second["data"]]
    assert len(ids) == len(set(ids)) == 4


@pytest.mark.asyncio
async def test_aggregates_hide_blocked_accounts(client, create_user, make_post):
    _, _, alice = await create_user("p48_ag_alice")
    _, _, bob = await create_user("p48_ag_bob")
    await make_post(bob, "blocked #p48blocktag")

    guest_tags = {
        t["tag"] for t in (await client.get("/api/page48/tags/trending")).json()["tags"]
    }
    assert "p48blocktag" in guest_tags

    await client.post("/api/page48/users/p48_ag_bob/block", headers=alice)

    alice_tags = {
        t["tag"]
        for t in (await client.get("/api/page48/tags/trending", headers=alice)).json()[
            "tags"
        ]
    }
    assert "p48blocktag" not in alice_tags

    guest_active = {
        u["username"]
        for u in (await client.get("/api/page48/users/active")).json()["users"]
    }
    assert "p48_ag_bob" in guest_active

    alice_active = {
        u["username"]
        for u in (await client.get("/api/page48/users/active", headers=alice)).json()[
            "users"
        ]
    }
    assert "p48_ag_bob" not in alice_active


@pytest.mark.asyncio
async def test_edit_updates_search_index(client, create_user, make_post):
    _, _, author = await create_user("p48_ei_author")
    post = await make_post(author, "alpha foxtrot")
    _, _, searcher = await create_user("p48_ei_searcher")

    before = (
        await client.get("/api/page48/search/posts?query=alpha", headers=searcher)
    ).json()
    assert len(before["data"]) == 1

    await client.patch(
        f"/api/page48/posts/{post['postId']}",
        json={"content": "omega foxtrot"},
        headers=author,
    )

    stale = (
        await client.get("/api/page48/search/posts?query=alpha", headers=searcher)
    ).json()
    assert stale["data"] == []

    fresh = (
        await client.get("/api/page48/search/posts?query=omega", headers=searcher)
    ).json()
    assert len(fresh["data"]) == 1


@pytest.mark.asyncio
async def test_feed_media_video_filter(client, create_user, storage_service):
    _, user_id, headers = await create_user("p48_fv_user")
    await client.post(
        "/api/page48/posts",
        json={
            "content": "clip",
            "videos": [
                {
                    "filename": f"page48/{user_id}/c.mp4",
                    "width": 1080,
                    "height": 1920,
                    "duration": 3,
                }
            ],
        },
        headers=headers,
    )

    videos = (await client.get("/api/page48/feed?media=video")).json()["data"]
    assert len(videos) == 1
    assert videos[0]["videos"]

    images = (await client.get("/api/page48/feed?media=image")).json()["data"]
    assert images == []


@pytest.mark.asyncio
async def test_notification_overview_per_tab(client, create_user, make_post, follow):
    _, _, user = await create_user("p48_ov_user")
    post = await make_post(user, "overview post")

    _, _, liker = await create_user("p48_ov_liker")
    await client.post(f"/api/page48/posts/{post['postId']}/like", headers=liker)
    await follow(liker, "p48_ov_user")

    overview = (
        await client.get("/api/page48/notifications/overview", headers=user)
    ).json()
    assert overview["total"] >= 2

    tabs = {t["tab"]: t for t in overview["tabs"]}
    assert tabs["likes"]["count"] == 1
    assert tabs["likes"]["previews"]
    assert tabs["follows"]["count"] == 1


# --------------------------------------------------------------------------- #
# Visibility must gate interactions, not just reads
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_interactions_refuse_hidden_posts(client, create_user, make_post):
    _, _, author = await create_user("p48_hid_author")
    post = await make_post(author, "hidden target")

    # The author blocks the actor, so the post is invisible to them.
    _, _, actor = await create_user("p48_hid_actor")
    await client.post("/api/page48/users/p48_hid_actor/block", headers=author)

    assert (
        await client.get(f"/api/page48/posts/{post['postId']}", headers=actor)
    ).status_code == 404

    for action in ("like", "repost", "bookmark"):
        res = await client.post(
            f"/api/page48/posts/{post['postId']}/{action}", headers=actor
        )
        assert res.status_code == 404

    # Reporting answers "invalid target", exactly like an unknown id, so the
    # response cannot be used to probe for hidden posts.
    assert (
        await client.post(
            "/api/page48/reports",
            json={"targetType": "post", "targetId": post["postId"], "reason": "spam"},
            headers=actor,
        )
    ).status_code == 400

    assert (
        await client.post(
            "/api/page48/posts",
            json={"content": "quoting hidden", "quotedPostId": post["postId"]},
            headers=actor,
        )
    ).status_code == 404

    assert (
        await client.post(
            "/api/page48/posts",
            json={"content": "replying hidden", "parentPostId": post["postId"]},
            headers=actor,
        )
    ).status_code == 404


@pytest.mark.asyncio
async def test_interactions_refuse_private_posts(client, create_user, make_post):
    _, _, author = await create_user("p48_privint_author")
    post = await make_post(author, "private target")
    await client.post(f"/api/page48/posts/{post['postId']}/private", headers=author)

    _, _, actor = await create_user("p48_privint_actor")
    for action in ("like", "repost", "bookmark"):
        assert (
            await client.post(
                f"/api/page48/posts/{post['postId']}/{action}", headers=actor
            )
        ).status_code == 404

    assert (
        await client.post(
            "/api/page48/reports",
            json={"targetType": "post", "targetId": post["postId"], "reason": "spam"},
            headers=actor,
        )
    ).status_code == 400

    # The owner may still read and report their own post (self-report is caught).
    assert (
        await client.get(f"/api/page48/posts/{post['postId']}", headers=author)
    ).status_code == 200


@pytest.mark.asyncio
async def test_poll_vote_refused_on_hidden_post(client, create_user):
    _, _, author = await create_user("p48_hidpoll_author")
    created = await client.post(
        "/api/page48/posts",
        json={"content": "hidden poll", "poll": {"options": ["a", "b"]}},
        headers=author,
    )
    body = created.json()
    option_id = body["poll"]["options"][0]["id"]
    await client.post(f"/api/page48/posts/{body['postId']}/private", headers=author)

    _, _, voter = await create_user("p48_hidpoll_voter")
    res = await client.post(
        f"/api/page48/posts/{body['postId']}/poll/vote",
        json={"optionId": option_id},
        headers=voter,
    )
    assert res.status_code == 404


# --------------------------------------------------------------------------- #
# Image references must stay inside the uploader's own prefix
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_create_post_rejects_foreign_image_reference(client, create_user):
    _, user_id, headers = await create_user("p48_img_ref")

    # A reference under the caller's own prefix is accepted.
    ok = await client.post(
        "/api/page48/posts",
        json={
            "content": "own image",
            "images": [{"filename": f"page48/{user_id}/a.webp"}],
        },
        headers=headers,
    )
    assert ok.status_code == 201, ok.text

    bad_refs = [
        # Another service's / user's stored object: the read side would sign it.
        "tickets/someone/evidence.webp",
        "avatar/someone/photo.webp",
        "page48/other-user/x.webp",
        # Traversal that still satisfies the prefix check.
        f"page48/{user_id}/../../tickets/x.webp",
        # External / inline payloads via the storage service passthrough.
        "https://evil.example/x.jpg",
        "data:image/svg+xml;base64,AAAA",
    ]
    for filename in bad_refs:
        res = await client.post(
            "/api/page48/posts",
            json={"content": "bad image", "images": [{"filename": filename}]},
            headers=headers,
        )
        assert res.status_code == 400, f"{filename} -> {res.status_code}"

    # Thread items go through the same check.
    thread = await client.post(
        "/api/page48/posts/thread",
        json={
            "posts": [
                {"content": "one"},
                {"content": "two", "images": [{"filename": "tickets/x/y.webp"}]},
            ]
        },
        headers=headers,
    )
    assert thread.status_code == 400


# --------------------------------------------------------------------------- #
# Block / mute lists are bounded at write time
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_block_relation_limit(client, create_user, monkeypatch):
    monkeypatch.setattr("src.page48.service.MAX_BLOCK_RELATIONS", 1)
    _, _, alice = await create_user("p48_bl_alice")
    _, _, _bob = await create_user("p48_bl_bob")
    _, _, _carol = await create_user("p48_bl_carol")

    first = await client.post("/api/page48/users/p48_bl_bob/block", headers=alice)
    assert first.status_code == 200

    # The second block is refused while the first still occupies the slot.
    second = await client.post("/api/page48/users/p48_bl_carol/block", headers=alice)
    assert second.status_code == 400

    # Freeing a slot lets the next block through.
    await client.delete("/api/page48/users/p48_bl_bob/block", headers=alice)
    third = await client.post("/api/page48/users/p48_bl_carol/block", headers=alice)
    assert third.status_code == 200


@pytest.mark.asyncio
async def test_mute_relation_limit(client, create_user, monkeypatch):
    monkeypatch.setattr("src.page48.service.MAX_MUTE_RELATIONS", 1)
    _, _, alice = await create_user("p48_mu_alice")
    _, _, _bob = await create_user("p48_mu_bob")
    _, _, _carol = await create_user("p48_mu_carol")

    first = await client.post("/api/page48/users/p48_mu_bob/mute", headers=alice)
    assert first.status_code == 200

    second = await client.post("/api/page48/users/p48_mu_carol/mute", headers=alice)
    assert second.status_code == 400

    await client.delete("/api/page48/users/p48_mu_bob/mute", headers=alice)
    third = await client.post("/api/page48/users/p48_mu_carol/mute", headers=alice)
    assert third.status_code == 200
