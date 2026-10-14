"""Post MyPage48 notifications to the Page48 social feed.

Mirrors ``telegram_notifier`` one channel over: the same caption builders from
``formatters`` feed a Page48 post instead of a Telegram message. Captions keep their
formatting, converted from Telegram HTML into Page48 display markers, and a caption
longer than the post limit becomes a chain of replies; any images Telegram would attach
are uploaded to storage first. A live's start, end and recap notifications are chained
into a single thread (the newest post is remembered per live id), so they read together
even though they are sent hours apart. The recorder posts as a dedicated (non-admin)
official Page48 account, whose API key is supplied via ``REC_PAGE48_API_KEY``.
"""

import base64
import html as html_module
import io
import json
import logging
import os
import random
import re
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from PIL import Image

from ..config import RecorderConfig
from ..models import LiveInfo
from .formatters import (
    _format_birthday_caption,
    _format_daily_schedule_caption,
    _format_end_live_caption,
    _format_health_caption,
    _format_idn_live_plus_caption,
    _format_live_start_caption,
    _format_monthly_birthday_caption,
    _format_news_caption,
    _format_recap_end_live_caption,
    _format_recap_gallery_caption,
    _format_replay_live_caption,
    _format_schedule_caption,
    _format_upcoming_schedule_caption,
)
from .media import LIVE_DETAIL_BASE_URL, _process_and_split_image
from .web_screenshot import capture_web_screenshot

log = logging.getLogger("notify")

# A Page48 post holds up to 2000 characters; longer captions become a thread.
PAGE48_MAX_CONTENT = 2000
PAGE48_MAX_POSTS = 50
PAGE48_MAX_MEDIA = 10
PAGE48_IMAGE_CATEGORY = "page48"
# Live start, end and recap share one Page48 thread, keyed by the live id, so the newest
# post of a live is remembered on disk between events (they are hours apart).
PAGE48_THREAD_STATE_FILE = "page48_live_threads.json"
PAGE48_THREAD_STATE_MAX = 300
# Member X handles rarely change, so the lookup is cached in memory: the endpoint is
# hit at most once per TTL per process, and a failed fetch retries sooner than that.
SOCIALS_TTL_SECONDS = 12 * 3600
SOCIALS_RETRY_SECONDS = 300
_socials_cache: dict = {"next": 0.0, "by_key": {}}

_ANCHOR_OPEN_RE = re.compile(
    r"<a\s+href=['\"]([^'\"]+)['\"][^>]*>", re.IGNORECASE | re.DOTALL
)
_TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
# HTML tag → the Page48 display marker it maps to (symmetric: same on open and close).
_STYLE_TAGS = {
    "b": "**",
    "strong": "**",
    "i": "*",
    "em": "*",
    "u": "__",
    "s": "~~",
    "strike": "~~",
    "del": "~~",
    "code": "`",
    "pre": "`",
}
_MARKER_LITERAL_RE = re.compile(r"([\\*_~`|])")


def _enabled(config: RecorderConfig) -> bool:
    return bool(config.page48_enabled and config.page48_api_key)


def _auth_headers(config: RecorderConfig) -> dict:
    return {"Authorization": f"Bearer {config.page48_api_key}"}


def _thread_state_path(config: RecorderConfig) -> str:
    return os.path.join(config.logs_dir, PAGE48_THREAD_STATE_FILE)


def _load_threads(config: RecorderConfig) -> dict:
    """Read the live-id -> newest post-id map, tolerating a missing/corrupt file."""
    try:
        with open(_thread_state_path(config)) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        log.warning("Page48 could not read thread state: %s", e)
        return {}


def _remember_thread(config: RecorderConfig, live_id: str, post_id: str) -> None:
    """Remember a live's newest post so the next event can reply to it."""
    if not live_id or not post_id:
        return
    threads = _load_threads(config)
    threads[live_id] = {
        "postId": post_id,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    if len(threads) > PAGE48_THREAD_STATE_MAX:
        newest = sorted(threads.items(), key=lambda item: item[1].get("at", ""))
        threads = dict(newest[-PAGE48_THREAD_STATE_MAX:])
    path = _thread_state_path(config)
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(threads, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log.warning("Page48 could not write thread state: %s", e)


def _thread_parent(config: RecorderConfig, live_id: str) -> Optional[str]:
    """The post this live's next notification should reply to, if any."""
    if not live_id:
        return None
    entry = _load_threads(config).get(live_id)
    return entry.get("postId") if isinstance(entry, dict) else None


async def _load_x_handles(config: RecorderConfig) -> dict:
    """Map lower-cased member name/nickname -> X account row, cached in memory."""
    now = time.monotonic()
    if now < _socials_cache["next"]:
        return _socials_cache["by_key"]

    url = f"{config.api_base_url.rstrip('/')}/members/socials/x"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
        if not resp.is_success:
            log.warning("Page48 member socials failed: %s", resp.status_code)
            _socials_cache["next"] = now + SOCIALS_RETRY_SECONDS
            return _socials_cache["by_key"]
        rows = resp.json()
    except Exception as e:
        log.warning("Page48 member socials error: %s", e)
        _socials_cache["next"] = now + SOCIALS_RETRY_SECONDS
        return _socials_cache["by_key"]

    by_key: dict = {}
    for row in rows if isinstance(rows, list) else []:
        if not (row or {}).get("username"):
            continue
        for key in (row.get("name"), row.get("nickname")):
            if key:
                by_key[str(key).strip().lower()] = row
    _socials_cache["by_key"] = by_key
    _socials_cache["next"] = now + SOCIALS_TTL_SECONDS
    return by_key


def _hashtag_word(value: str) -> str:
    """Strip anything that cannot live in a `#hashtag` (keeps letters/digits/_)."""
    return re.sub(r"[^\w]", "", value or "", flags=re.UNICODE)


async def _x_row(
    config: RecorderConfig, member_name: str, member_nickname: str
) -> Optional[dict]:
    """The X account row for a member, matched by nickname then name."""
    handles = await _load_x_handles(config)
    for key in (member_nickname, member_name):
        if key:
            row = handles.get(str(key).strip().lower())
            if row:
                return row
    return None


async def _member_hashtags(
    config: RecorderConfig, member_name: str, member_nickname: str
) -> str:
    """Page48-only trailing hashtag for a live post: `#NicknameJKT48`.

    Built from the member's nickname in the members API (the same source the Page48
    sidebar uses), so a post's tag matches the one the sidebar links to; it falls back
    to the live's own nickname when the member is not in that list.
    """
    row = await _x_row(config, member_name, member_nickname)
    if row:
        source = row.get("nickname") or row.get("name")
    else:
        source = member_nickname or member_name

    nickname = _hashtag_word(source)
    if not nickname:
        return ""
    if not nickname.lower().endswith("jkt48"):
        nickname += "JKT48"
    return f"#{nickname}"


def _escape_markers(text: str) -> str:
    """Backslash-escape marker characters so caption text never triggers formatting."""
    return _MARKER_LITERAL_RE.sub(r"\\\1", text)


def _html_to_markers(text: str) -> str:
    """Convert a Telegram HTML caption into Page48 display markers.

    Bold/italic/underline/strike/code keep their styling and links become
    ``[label](url)``, so a Page48 notification reads like its Telegram original. Loose
    marker characters in the caption body are escaped so literal text cannot trigger
    formatting.
    """
    if not text:
        return ""

    out: list[str] = []
    anchor_stack: list[str] = []

    for token in _TAG_SPLIT_RE.split(text):
        if not token:
            continue

        if not token.startswith("<"):
            out.append(_escape_markers(html_module.unescape(token)))
            continue

        anchor = _ANCHOR_OPEN_RE.match(token)
        if anchor:
            anchor_stack.append(anchor.group(1))
            out.append("[")
            continue

        name = token.strip("</> ").lower()
        if token.startswith("</"):
            if name == "a":
                url = anchor_stack.pop() if anchor_stack else ""
                out.append(f"]({url})")
            elif name in _STYLE_TAGS:
                out.append(_STYLE_TAGS[name])
        elif name in _STYLE_TAGS:
            out.append(_STYLE_TAGS[name])
        # Any other tag (e.g. <br>) is dropped; captions already use plain newlines.

    text = "".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _chunk_text(text: str, limit: int = PAGE48_MAX_CONTENT) -> list[str]:
    """Split text into <=limit chunks, preferring line boundaries."""
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        # Hard-split a single line that cannot fit on its own.
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]

        candidate = line if not current else f"{current}\n{line}"
        if len(candidate) > limit:
            if current:
                chunks.append(current)
            current = line
        else:
            current = candidate

    if current:
        chunks.append(current)

    chunks = [c for c in chunks if c]
    if len(chunks) > PAGE48_MAX_POSTS:
        log.warning(
            "Page48 notification needs %d posts; truncating to %d",
            len(chunks),
            PAGE48_MAX_POSTS,
        )
        chunks = chunks[:PAGE48_MAX_POSTS]
        chunks[-1] = chunks[-1][: PAGE48_MAX_CONTENT - 1] + "…"
    return chunks


def _image_meta(data: bytes) -> tuple:
    """Return (width, height, image format) for the given bytes."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = (img.format or "").lower() or "jpeg"
            return img.width, img.height, fmt
    except Exception:
        return 0, 0, "jpeg"


async def _load_image_bytes(client: httpx.AsyncClient, source: str) -> Optional[bytes]:
    """Read an image from a local path or a remote URL, best effort."""
    if not source:
        return None
    try:
        if str(source).startswith("http"):
            resp = await client.get(source, timeout=30.0)
            if resp.is_success:
                return resp.content
            log.warning("Page48 image fetch failed: %s %s", source, resp.status_code)
            return None
        if os.path.exists(source):
            with open(source, "rb") as f:
                return f.read()
    except Exception as e:
        log.warning("Page48 failed to read image %s: %s", source, e)
    return None


async def _upload_image(
    client: httpx.AsyncClient, config: RecorderConfig, data: bytes
) -> Optional[dict]:
    """Upload one image to storage; returns a Page48 media ref or None."""
    url = f"{config.page48_api_base_url}/storage/upload"
    width, height, fmt = _image_meta(data)
    # The endpoint expects a data URI (it re-encodes to webp and ignores the subtype).
    encoded = base64.b64encode(data).decode("ascii")
    payload = {
        "image": f"data:image/{fmt};base64,{encoded}",
        "category": PAGE48_IMAGE_CATEGORY,
    }
    try:
        resp = await client.post(url, json=payload, headers=_auth_headers(config))
        if not resp.is_success:
            log.warning(
                "Page48 image upload failed: %s %s", resp.status_code, resp.text
            )
            return None
        filename = (resp.json() or {}).get("filename")
        if not filename:
            return None
        return {"type": "image", "filename": filename, "width": width, "height": height}
    except Exception:
        log.exception("Exception during Page48 image upload")
        return None


async def _create_post(
    client: httpx.AsyncClient,
    config: RecorderConfig,
    content: str,
    media: list,
    parent_post_id: Optional[str] = None,
) -> Optional[str]:
    """Create one Page48 post; returns its id, or None on failure."""
    url = f"{config.page48_api_base_url}/page48/posts"
    payload: dict = {"content": content, "media": media or []}
    if parent_post_id:
        payload["parentPostId"] = parent_post_id
    try:
        resp = await client.post(url, json=payload, headers=_auth_headers(config))
        if not resp.is_success:
            log.error("Page48 post failed: %s %s", resp.status_code, resp.text)
            return None
        return (resp.json() or {}).get("postId")
    except Exception:
        log.exception("Exception during Page48 post")
        return None


async def _publish(
    config: RecorderConfig,
    caption_html: str,
    image_sources: Optional[list[str]] = None,
    parent_post_id: Optional[str] = None,
    thread_key: Optional[str] = None,
    hashtags: Optional[str] = None,
) -> bool:
    """Convert a caption, upload its images, and post it to Page48.

    A caption longer than the post limit becomes a chain of replies (not separate
    posts), and `parent_post_id` makes the whole notification hang off an earlier one.
    Together these let a live's start, end and recap read as a single thread even
    though they are sent hours apart; `thread_key` (the live id) remembers the newest
    post so the next event can continue it. `hashtags` (already marker text) is appended
    last, after conversion, so its `#`/`_` are never escaped.
    """
    if not _enabled(config):
        return False

    text = _html_to_markers(caption_html)
    if not text:
        return False

    if hashtags:
        text = f"{text}\n\n{hashtags}"

    image_sources = [s for s in (image_sources or []) if s]

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            media: list = []
            for source in image_sources[:PAGE48_MAX_MEDIA]:
                data = await _load_image_bytes(client, source)
                if not data:
                    continue
                item = await _upload_image(client, config, data)
                if item:
                    media.append(item)

            chunks = _chunk_text(text)
            parent = parent_post_id
            last_post_id: Optional[str] = None
            for index, chunk in enumerate(chunks):
                # Uploaded media rides on the first post of this notification only.
                post_id = await _create_post(
                    client, config, chunk, media if index == 0 else [], parent
                )
                if not post_id:
                    log.error(
                        "Page48 notification aborted at post %d/%d",
                        index + 1,
                        len(chunks),
                    )
                    break
                last_post_id = post_id
                parent = post_id

            if last_post_id and thread_key:
                _remember_thread(config, thread_key, last_post_id)
            return last_post_id is not None
    except Exception:
        log.exception("Exception during Page48 notification")
        return False


async def _collect_recap_web_image(live_id: str, folder_path: str) -> list[str]:
    """The gift-recap web screenshot (the reward table) for the recap post."""
    images: list[str] = []
    if not folder_path:
        return images

    web_path = os.path.join(folder_path, f"{live_id}_web.png")
    try:
        url = f"{LIVE_DETAIL_BASE_URL}/{live_id}"
        ok = await capture_web_screenshot(url, web_path)
        if ok and os.path.exists(web_path):
            images.extend(_process_and_split_image(web_path))
    except Exception as e:
        log.warning("Page48 web screenshot failed, continuing: %s", e)

    return images


def _collect_live_screenshots(folder_path: str) -> list[str]:
    """Every live screenshot on disk, for the separate gallery post."""
    if not folder_path:
        return []
    screenshot_dir = os.path.join(folder_path, "screenshots")
    if not os.path.isdir(screenshot_dir):
        return []
    return [
        os.path.join(screenshot_dir, name)
        for name in sorted(os.listdir(screenshot_dir))
        if name.endswith(".jpg")
    ]


async def send_live_start_notification(live: LiveInfo, config: RecorderConfig) -> bool:
    """Post a Page48 notification when a live stream starts."""
    if not _enabled(config):
        return False
    log.info("Sending live start Page48 notification for %s", live.live_id)
    hashtags = await _member_hashtags(config, live.member_name, live.member_nickname)
    return await _publish(
        config,
        _format_live_start_caption(live),
        [live.image or live.member_image],
        thread_key=live.live_id,
        hashtags=hashtags,
    )


async def send_end_live_notification(config: RecorderConfig, data: dict) -> bool:
    """Post a Page48 notification when a live stream ends."""
    if not _enabled(config):
        return False
    live_id = str(data.get("live_id") or "")
    log.info("Sending simple end live Page48 notification")
    hashtags = await _member_hashtags(
        config,
        str(data.get("member_name") or ""),
        str(data.get("member_nickname") or ""),
    )
    return await _publish(
        config,
        _format_end_live_caption(data),
        parent_post_id=_thread_parent(config, live_id),
        thread_key=live_id or None,
        hashtags=hashtags,
    )


async def send_recap_end_live_notification(
    live_id: str, config: RecorderConfig, folder_path: str = ""
) -> bool:
    """Fetch replay data and post a recap notification to Page48."""
    if not _enabled(config):
        log.info("Page48 not configured. Skipping.")
        return False

    api_url = f"{config.api_base_url.rstrip('/')}/replays/{live_id}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(api_url)
            if not resp.is_success:
                log.error(
                    "Failed to fetch replay data: %s %s", resp.status_code, resp.text
                )
                return False
            data = resp.json()

        live_type = "public"
        if folder_path:
            meta_path = os.path.join(folder_path, f"{live_id}.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path) as f:
                        meta = json.load(f)
                        live_type = meta.get("live_type", "public")
                except Exception:
                    pass

        caption = _format_recap_end_live_caption(
            data, live_id=live_id, live_type=live_type
        )
        hashtags = await _member_hashtags(
            config,
            str(data.get("member_name") or ""),
            str(data.get("member_nickname") or ""),
        )
        # The recap itself carries only the gift-recap web screenshot; the live's own
        # screenshots go up as a separate gallery post below.
        web_images = await _collect_recap_web_image(live_id, folder_path)
        ok = await _publish(
            config,
            caption,
            web_images,
            parent_post_id=_thread_parent(config, live_id),
            thread_key=live_id,
            hashtags=hashtags,
        )

        # A standalone album (a new root post, not a reply on the live thread).
        shots = _collect_live_screenshots(folder_path)
        if shots:
            picked = random.sample(shots, min(PAGE48_MAX_MEDIA, len(shots)))
            log.info(
                "Posting Page48 live gallery for %s (%d of %d screenshots)",
                live_id,
                len(picked),
                len(shots),
            )
            await _publish(
                config,
                _format_recap_gallery_caption(
                    data, live_id=live_id, live_type=live_type
                ),
                picked,
                hashtags=hashtags,
            )

        return ok
    except Exception:
        log.exception("Exception during Page48 recap notification for %s:", live_id)
        return False


async def send_replay_live_notification(
    live_id: str,
    youtube_title: str,
    youtube_id: str,
    config: RecorderConfig,
    folder_path: str,
) -> bool:
    """Post a Page48 notification for a new YouTube replay."""
    if not _enabled(config):
        return False
    log.info("Sending replay live Page48 notification for %s", live_id)

    meta_path = os.path.join(folder_path, f"{live_id}.json")
    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path) as f:
                meta = json.load(f)
        except Exception:
            pass

    caption = _format_replay_live_caption(meta, youtube_title, youtube_id)
    thumb = os.path.join(folder_path, f"{live_id}_yt_thumb.jpg")
    return await _publish(config, caption, [thumb])


async def send_news_notification(news_data: dict, config: RecorderConfig) -> bool:
    """Post a Page48 notification for new JKT48 news."""
    if not _enabled(config):
        return False
    log.info("Sending news Page48 notification for %s", news_data.get("news_id"))

    sources: list[str] = []
    screenshot_path = news_data.get("screenshot_path")
    if screenshot_path and os.path.exists(screenshot_path):
        sources.append(screenshot_path)
    for img_path in news_data.get("article_images", []):
        if os.path.exists(img_path):
            sources.append(img_path)
        if len(sources) >= PAGE48_MAX_MEDIA:
            break

    return await _publish(config, _format_news_caption(news_data), sources)


async def send_schedule_notification(payload: dict, config: RecorderConfig) -> bool:
    """Post a Page48 notification for new or updated schedules."""
    if not _enabled(config):
        return False
    log.info("Sending schedule Page48 notification")

    screenshot_paths = payload.get("screenshot_paths") or []
    single = payload.get("screenshot_path")
    if not screenshot_paths and single:
        screenshot_paths = [single]
    sources = [str(p) for p in screenshot_paths if p and os.path.exists(str(p))]

    return await _publish(config, _format_schedule_caption(payload), sources)


async def send_idn_live_plus_notification(
    payload: dict, config: RecorderConfig
) -> bool:
    """Post a Page48 notification for new or updated IDN Live Plus schedules."""
    if not _enabled(config):
        return False
    log.info("Sending IDN Live Plus schedule Page48 notification")

    sources = []
    screenshot_path = payload.get("screenshot_path")
    if screenshot_path and os.path.exists(screenshot_path):
        sources.append(screenshot_path)

    return await _publish(config, _format_idn_live_plus_caption(payload), sources)


async def send_daily_schedule_reminder(payload: dict, config: RecorderConfig) -> bool:
    """Post the daily reminder of today's schedules to Page48."""
    schedules = payload.get("schedules", [])
    if not schedules:
        return True
    if not _enabled(config):
        return False
    return await _publish(config, _format_daily_schedule_caption(payload))


async def send_upcoming_schedule_reminder(sch: dict, config: RecorderConfig) -> bool:
    """Post an upcoming (H-30) schedule reminder to Page48."""
    if not _enabled(config):
        return False
    return await _publish(config, _format_upcoming_schedule_caption(sch))


async def send_birthday_notification(member: dict, config: RecorderConfig) -> bool:
    """Post a birthday notification to Page48."""
    if not _enabled(config):
        return False
    return await _publish(
        config, _format_birthday_caption(member), [member.get("img", "")]
    )


async def send_monthly_birthday_list(
    month_name: str, members: list, config: RecorderConfig
) -> bool:
    """Post the monthly birthday list to Page48."""
    if not members:
        return True
    if not _enabled(config):
        return False
    return await _publish(config, _format_monthly_birthday_caption(month_name, members))


async def send_health_notification(payload: dict, config: RecorderConfig) -> bool:
    """Post a health status change notification to Page48."""
    if not payload.get("changes"):
        return True
    if not _enabled(config):
        return False
    return await _publish(config, _format_health_caption(payload))
