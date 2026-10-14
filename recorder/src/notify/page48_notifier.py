"""Post MyPage48 notifications to the Page48 social feed.

Mirrors ``telegram_notifier`` one channel over: the same caption builders from
``formatters`` feed a Page48 post instead of a Telegram message. Captions keep their
formatting, converted from Telegram HTML into Page48 display markers, and are split into
a thread when longer than the post limit; any images Telegram would attach are uploaded
to storage first. The recorder posts as a dedicated (non-admin) official Page48 account,
whose API key is supplied via ``REC_PAGE48_API_KEY``.
"""

import base64
import html as html_module
import io
import json
import logging
import os
import re
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
    client: httpx.AsyncClient, config: RecorderConfig, content: str, media: list
) -> bool:
    url = f"{config.page48_api_base_url}/page48/posts"
    try:
        resp = await client.post(
            url,
            json={"content": content, "media": media or []},
            headers=_auth_headers(config),
        )
        if not resp.is_success:
            log.error("Page48 post failed: %s %s", resp.status_code, resp.text)
            return False
        return True
    except Exception:
        log.exception("Exception during Page48 post")
        return False


async def _create_thread(
    client: httpx.AsyncClient, config: RecorderConfig, contents: list, media: list
) -> bool:
    url = f"{config.page48_api_base_url}/page48/posts/thread"
    posts = [{"content": c} for c in contents]
    if media:
        posts[0]["media"] = media
    try:
        resp = await client.post(
            url, json={"posts": posts}, headers=_auth_headers(config)
        )
        if not resp.is_success:
            log.error("Page48 thread failed: %s %s", resp.status_code, resp.text)
            return False
        return True
    except Exception:
        log.exception("Exception during Page48 thread")
        return False


async def _publish(
    config: RecorderConfig,
    caption_html: str,
    image_sources: Optional[list[str]] = None,
) -> bool:
    """Convert a caption, upload its images, and post it to Page48."""
    if not _enabled(config):
        return False

    text = _html_to_markers(caption_html)
    if not text:
        return False

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
            if len(chunks) == 1:
                return await _create_post(client, config, chunks[0], media)
            return await _create_thread(client, config, chunks, media)
    except Exception:
        log.exception("Exception during Page48 notification")
        return False


async def _collect_recap_images(live_id: str, folder_path: str) -> list[str]:
    """Local image paths for a recap, mirroring the Telegram image set."""
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

    screenshot_dir = os.path.join(folder_path, "screenshots")
    if os.path.isdir(screenshot_dir):
        for fname in sorted(os.listdir(screenshot_dir)):
            if fname.endswith(".jpg"):
                images.append(os.path.join(screenshot_dir, fname))
                if len(images) >= 5:
                    break

    return images


async def send_live_start_notification(live: LiveInfo, config: RecorderConfig) -> bool:
    """Post a Page48 notification when a live stream starts."""
    if not _enabled(config):
        return False
    log.info("Sending live start Page48 notification for %s", live.live_id)
    return await _publish(
        config, _format_live_start_caption(live), [live.image or live.member_image]
    )


async def send_end_live_notification(config: RecorderConfig, data: dict) -> bool:
    """Post a Page48 notification when a live stream ends."""
    if not _enabled(config):
        return False
    log.info("Sending simple end live Page48 notification")
    return await _publish(config, _format_end_live_caption(data))


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
        images = await _collect_recap_images(live_id, folder_path)
        return await _publish(config, caption, images)
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
