import json
import logging
import os

import httpx

from ..config import RecorderConfig
from ..models import LiveInfo
from .formatters import (
    _format_birthday_caption,
    _format_daily_schedule_caption,
    _format_date_only_wib,
    _format_date_wib,
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

# Re-exported so existing importers (schedule/news checkers) keep working.
__all__ = [
    "_format_date_only_wib",
    "_format_date_wib",
    "send_end_live_notification",
    "send_recap_end_live_notification",
    "send_replay_live_notification",
    "send_live_start_notification",
    "send_news_notification",
    "send_schedule_notification",
    "send_daily_schedule_reminder",
    "send_birthday_notification",
    "send_upcoming_schedule_reminder",
    "send_monthly_birthday_list",
    "send_idn_live_plus_notification",
    "send_health_notification",
]

log = logging.getLogger("notify")


def _is_enabled(config: RecorderConfig) -> bool:
    """Telegram is enabled only when the toggle is on and creds are present."""
    return bool(
        config.telegram_enabled
        and config.telegram_bot_token
        and config.telegram_chat_id
    )


async def send_end_live_notification(config: RecorderConfig, data: dict) -> bool:
    """Send a simple notification to Telegram when a live stream ends."""
    if not _is_enabled(config):
        return False

    log.info("Sending simple end live Telegram notification")

    caption = _format_end_live_caption(data)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            tg_url = (
                f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
            )
            tg_data = {
                "chat_id": config.telegram_chat_id,
                "text": caption,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }

            tg_resp = await client.post(tg_url, json=tg_data)
            if not tg_resp.is_success:
                log.error("Simple end live notification failed: %s", tg_resp.text)
                return False

            return True
    except Exception:
        log.exception("Exception during simple end live notification:")
        return False


async def send_recap_end_live_notification(
    live_id: str, config: RecorderConfig, folder_path: str = ""
) -> bool:
    """Fetch replay data and send a recap notification to Telegram."""
    if not _is_enabled(config):
        log.info("Telegram not configured (bot token or chat ID missing). Skipping.")
        return False

    api_url = f"{config.api_base_url.rstrip('/')}/replays/{live_id}"
    log.info("Fetching replay data for Telegram recap notification from %s", api_url)

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

            images_to_send = []

            # 1. Try web screenshot first (non-blocking: failure won't stop notification)
            if folder_path:
                web_screenshot_path = os.path.join(folder_path, f"{live_id}_web.png")
                try:
                    url = f"{LIVE_DETAIL_BASE_URL}/{live_id}"
                    success = await capture_web_screenshot(url, web_screenshot_path)
                    if success and os.path.exists(web_screenshot_path):
                        split_paths = _process_and_split_image(web_screenshot_path)
                        for idx, p in enumerate(split_paths):
                            suffix = f"_pt{idx+1}" if len(split_paths) > 1 else ""
                            images_to_send.append((f"web{suffix}", p))
                except Exception as e:
                    log.warning("Web screenshot failed, continuing: %s", e)

            # 2. Add cover/thumbnail image
            # if folder_path:
            #     yt_thumb = os.path.join(folder_path, f"{live_id}_yt_thumb.jpg")
            #     cover = os.path.join(folder_path, f"{live_id}.jpg")
            #     if os.path.exists(yt_thumb):
            #         images_to_send.append(("cover", yt_thumb))
            #     elif os.path.exists(cover):
            #         images_to_send.append(("cover", cover))

            # 2. Add screenshots (limit to max 4 total images)
            if folder_path:
                screenshot_dir = os.path.join(folder_path, "screenshots")
                if os.path.isdir(screenshot_dir):
                    for fname in sorted(os.listdir(screenshot_dir)):
                        if fname.endswith(".jpg"):
                            images_to_send.append(
                                (
                                    f"scr_{len(images_to_send)}",
                                    os.path.join(screenshot_dir, fname),
                                )
                            )
                            if len(images_to_send) >= 5:
                                break

            upload_success = False

            if len(images_to_send) > 1:
                log.info(
                    "Found %d images, sending as Telegram MediaGroup",
                    len(images_to_send),
                )
                import json

                tg_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMediaGroup"
                media = []
                files = {}
                for i, (name, path) in enumerate(images_to_send):
                    media_item = {"type": "photo", "media": f"attach://{name}"}
                    if i == 0:
                        media_item["caption"] = caption
                        media_item["parse_mode"] = "HTML"
                    media.append(media_item)
                    files[name] = (name + ".jpg", open(path, "rb"), "image/jpeg")

                try:
                    tg_resp = await client.post(
                        tg_url,
                        data={
                            "chat_id": config.telegram_chat_id,
                            "media": json.dumps(media),
                        },
                        files=files,
                    )
                    for _, f, _ in files.values():
                        f.close()
                    if tg_resp.is_success:
                        upload_success = True
                    else:
                        log.warning(
                            "Telegram MediaGroup failed: %s %s",
                            tg_resp.status_code,
                            tg_resp.text,
                        )
                except Exception:
                    for _, f, _ in files.values():
                        if not f.closed:
                            f.close()
                    log.exception("Exception during MediaGroup upload:")

            elif len(images_to_send) == 1:
                name, path = images_to_send[0]
                log.info("Found 1 image, sending as Telegram Photo")
                tg_url = (
                    f"https://api.telegram.org/bot{config.telegram_bot_token}/sendPhoto"
                )
                try:
                    with open(path, "rb") as f:
                        tg_resp = await client.post(
                            tg_url,
                            data={
                                "chat_id": config.telegram_chat_id,
                                "caption": caption,
                                "parse_mode": "HTML",
                            },
                            files={"photo": (name + ".jpg", f, "image/jpeg")},
                        )
                    if tg_resp.is_success:
                        upload_success = True
                    else:
                        log.warning(
                            "Telegram Photo failed: %s %s",
                            tg_resp.status_code,
                            tg_resp.text,
                        )
                except Exception:
                    log.exception("Exception during Photo upload:")

            if upload_success:
                log.info(
                    "Telegram notification sent successfully (with media) for %s",
                    live_id,
                )
                return True

            # If local upload fails or no local file, just send a text message
            tg_url = (
                f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
            )
            tg_data = {
                "chat_id": config.telegram_chat_id,
                "text": caption,
                "parse_mode": "HTML",
            }

            tg_resp = await client.post(tg_url, json=tg_data)
            if not tg_resp.is_success:
                log.error(
                    "Telegram notification failed: %s %s",
                    tg_resp.status_code,
                    tg_resp.text,
                )
                return False

            log.info("Telegram notification sent successfully for %s", live_id)
            return True

    except Exception:
        log.exception("Exception during Telegram notification for %s:", live_id)
        return False


async def send_replay_live_notification(
    live_id: str,
    youtube_title: str,
    youtube_id: str,
    config: RecorderConfig,
    folder_path: str,
) -> bool:
    """Send a Telegram notification for a new YouTube replay."""
    if not _is_enabled(config):
        return False

    log.info("Sending replay live Telegram notification for %s", live_id)

    # Read meta to get platform and member info
    meta_path = os.path.join(folder_path, f"{live_id}.json")
    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path) as f:
                meta = json.load(f)
        except Exception:
            pass

    caption = _format_replay_live_caption(meta, youtube_title, youtube_id)

    image_path = os.path.join(folder_path, f"{live_id}_yt_thumb.jpg")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if os.path.exists(image_path):
                tg_url = (
                    f"https://api.telegram.org/bot{config.telegram_bot_token}/sendPhoto"
                )
                try:
                    with open(image_path, "rb") as f:
                        tg_resp = await client.post(
                            tg_url,
                            data={
                                "chat_id": config.telegram_chat_id,
                                "caption": caption,
                                "parse_mode": "HTML",
                            },
                            files={"photo": ("thumbnail.jpg", f, "image/jpeg")},
                        )
                    if tg_resp.is_success:
                        return True
                    else:
                        log.warning(
                            "Telegram Photo failed: %s %s",
                            tg_resp.status_code,
                            tg_resp.text,
                        )
                except Exception:
                    log.exception(
                        "Exception during Photo upload for replay notification:"
                    )

            # Fallback to text message
            tg_url = (
                f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
            )
            tg_data = {
                "chat_id": config.telegram_chat_id,
                "text": caption,
                "parse_mode": "HTML",
            }

            tg_resp = await client.post(tg_url, json=tg_data)
            if not tg_resp.is_success:
                log.error(
                    "Telegram replay notification failed: %s %s",
                    tg_resp.status_code,
                    tg_resp.text,
                )
                return False

            return True
    except Exception:
        log.exception("Exception during Telegram replay notification for %s:", live_id)
        return False


async def send_live_start_notification(live: LiveInfo, config: RecorderConfig) -> bool:
    """Send a notification to Telegram when a live stream starts."""
    if not _is_enabled(config):
        return False

    log.info("Sending live start Telegram notification for %s", live.live_id)

    caption = _format_live_start_caption(live)

    # Priority: cover image > member avatar
    image_url = live.image or live.member_image

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            if image_url and str(image_url).startswith("http"):
                try:
                    head_resp = await client.head(image_url, timeout=5.0)
                    if not head_resp.is_success:
                        log.warning(
                            "Live start image URL %s returned %s, falling back to text",
                            image_url,
                            head_resp.status_code,
                        )
                        image_url = None
                except Exception as e:
                    log.warning("Failed to check live start image URL: %s", e)
                    image_url = None

            if image_url and str(image_url).startswith("http"):
                tg_url = (
                    f"https://api.telegram.org/bot{config.telegram_bot_token}/sendPhoto"
                )
                tg_data = {
                    "chat_id": config.telegram_chat_id,
                    "caption": caption,
                    "parse_mode": "HTML",
                    "photo": image_url,
                }
            else:
                tg_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
                tg_data = {
                    "chat_id": config.telegram_chat_id,
                    "text": caption,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                }

            tg_resp = await client.post(tg_url, json=tg_data)
            if not tg_resp.is_success:
                log.error("Live start notification failed: %s", tg_resp.text)
                return False

            return True
    except Exception:
        log.exception("Exception during live start notification:")
        return False


async def send_news_notification(news_data: dict, config: RecorderConfig) -> bool:
    """Send a notification to Telegram for new JKT48 news."""
    if not _is_enabled(config):
        return False

    log.info("Sending news Telegram notification for %s", news_data.get("news_id"))

    screenshot_path = news_data.get("screenshot_path")
    article_images = news_data.get("article_images", [])

    caption = _format_news_caption(news_data)

    images_to_send = []
    if screenshot_path and os.path.exists(screenshot_path):
        images_to_send.append(("news_screenshot", screenshot_path))

    for idx, img_path in enumerate(article_images):
        if os.path.exists(img_path):
            images_to_send.append((f"img_{idx}", img_path))
        if len(images_to_send) >= 10:  # Telegram MediaGroup max limit
            break

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            upload_success = False

            if len(images_to_send) > 1:
                import json

                log.info(
                    "Sending news notification with MediaGroup (%d images)",
                    len(images_to_send),
                )
                tg_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMediaGroup"
                media = []
                files = {}
                for i, (name, path) in enumerate(images_to_send):
                    media_item = {"type": "photo", "media": f"attach://{name}"}
                    if i == 0:
                        media_item["caption"] = caption
                        media_item["parse_mode"] = "HTML"
                    media.append(media_item)

                    ext = os.path.splitext(path)[1].lower()
                    mime_type = "image/png" if ext == ".png" else "image/jpeg"
                    files[name] = (name + ext, open(path, "rb"), mime_type)

                try:
                    tg_resp = await client.post(
                        tg_url,
                        data={
                            "chat_id": config.telegram_chat_id,
                            "media": json.dumps(media),
                        },
                        files=files,
                    )
                    for _, f, _ in files.values():
                        f.close()
                    if tg_resp.is_success:
                        upload_success = True
                    else:
                        log.warning(
                            "Telegram MediaGroup failed: %s %s",
                            tg_resp.status_code,
                            tg_resp.text,
                        )
                except Exception:
                    for _, f, _ in files.values():
                        if not f.closed:
                            f.close()
                    log.exception("Exception during MediaGroup upload:")

            elif len(images_to_send) == 1:
                name, path = images_to_send[0]
                log.info("Sending news notification with single Photo")
                tg_url = (
                    f"https://api.telegram.org/bot{config.telegram_bot_token}/sendPhoto"
                )
                try:
                    with open(path, "rb") as f:
                        ext = os.path.splitext(path)[1].lower()
                        mime_type = "image/png" if ext == ".png" else "image/jpeg"
                        tg_resp = await client.post(
                            tg_url,
                            data={
                                "chat_id": config.telegram_chat_id,
                                "caption": caption,
                                "parse_mode": "HTML",
                            },
                            files={"photo": (name + ext, f, mime_type)},
                        )
                    if tg_resp.is_success:
                        upload_success = True
                    else:
                        log.warning(
                            "Telegram Photo failed: %s %s",
                            tg_resp.status_code,
                            tg_resp.text,
                        )
                except Exception:
                    log.exception("Exception during Photo upload:")

            if upload_success:
                return True

            # Fallback to text message if screenshot failed or wasn't provided
            tg_url = (
                f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
            )
            tg_data = {
                "chat_id": config.telegram_chat_id,
                "text": caption,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            }

            tg_resp = await client.post(tg_url, json=tg_data)
            if not tg_resp.is_success:
                log.error("News notification failed: %s", tg_resp.text)
                return False

            return True
    except Exception:
        log.exception("Exception during news notification:")
        return False


async def send_schedule_notification(payload: dict, config: RecorderConfig) -> bool:
    """Send a notification to Telegram for new or updated schedules."""
    if not _is_enabled(config):
        return False

    log.info("Sending schedule Telegram notification")

    screenshot_paths = payload.get("screenshot_paths", [])
    if not screenshot_paths and payload.get("screenshot_path"):
        screenshot_paths = [payload.get("screenshot_path")]

    caption = _format_schedule_caption(payload)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            upload_success = False

            if screenshot_paths:
                valid_paths = [p for p in screenshot_paths if os.path.exists(p)]
                if len(valid_paths) == 1:
                    log.info("Sending schedule notification with Photo")
                    tg_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendPhoto"
                    try:
                        with open(valid_paths[0], "rb") as f:
                            tg_resp = await client.post(
                                tg_url,
                                data={
                                    "chat_id": config.telegram_chat_id,
                                    "caption": caption,
                                    "parse_mode": "HTML",
                                },
                                files={"photo": ("schedule.jpg", f, "image/jpeg")},
                            )
                        if tg_resp.is_success:
                            upload_success = True
                        else:
                            log.warning(
                                "Telegram Photo failed: %s %s",
                                tg_resp.status_code,
                                tg_resp.text,
                            )
                    except Exception:
                        log.exception("Exception during Photo upload:")
                elif len(valid_paths) > 1:
                    log.info(
                        f"Sending schedule notification with {len(valid_paths)} Photos in MediaGroup"
                    )
                    tg_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMediaGroup"

                    media_group = []
                    files = {}
                    import json

                    for i, path in enumerate(valid_paths[:10]):
                        filename = f"photo_{i}.jpg"
                        files[filename] = (filename, open(path, "rb"), "image/jpeg")

                        media_item = {"type": "photo", "media": f"attach://{filename}"}
                        if i == 0:
                            media_item["caption"] = caption
                            media_item["parse_mode"] = "HTML"

                        media_group.append(media_item)

                    try:
                        tg_resp = await client.post(
                            tg_url,
                            data={
                                "chat_id": config.telegram_chat_id,
                                "media": json.dumps(media_group),
                            },
                            files=files,
                        )
                        for f_tuple in files.values():
                            f_tuple[1].close()

                        if tg_resp.is_success:
                            upload_success = True
                        else:
                            log.warning(
                                "Telegram MediaGroup failed: %s %s",
                                tg_resp.status_code,
                                tg_resp.text,
                            )
                    except Exception:
                        log.exception("Exception during MediaGroup upload:")
                        for f_tuple in files.values():
                            f_tuple[1].close()

            if upload_success:
                return True

            # Fallback to text message
            tg_url = (
                f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
            )
            tg_resp = await client.post(
                tg_url,
                json={
                    "chat_id": config.telegram_chat_id,
                    "text": caption,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
            )
            if not tg_resp.is_success:
                log.error("Schedule notification failed: %s", tg_resp.text)
                return False

            return True

    except Exception:
        log.exception("Exception during schedule notification:")
        return False


async def send_daily_schedule_reminder(payload: dict, config: RecorderConfig) -> bool:
    """Send a daily reminder of today's schedules."""
    if not _is_enabled(config):
        return False

    schedules = payload.get("schedules", [])
    if not schedules:
        return True

    caption = _format_daily_schedule_caption(payload)

    tg_url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            tg_resp = await client.post(
                tg_url,
                json={
                    "chat_id": config.telegram_chat_id,
                    "text": caption,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
            if not tg_resp.is_success:
                log.error("Daily reminder notification failed: %s", tg_resp.text)
                return False

            return True

    except Exception:
        log.exception("Exception during daily reminder notification:")
        return False


async def send_birthday_notification(member: dict, config) -> bool:
    if not _is_enabled(config):
        return False

    img_url = member.get("img", "")

    caption = _format_birthday_caption(member)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            upload_success = False

            if img_url:
                log.info("Sending birthday notification with Photo")
                tg_url = (
                    f"https://api.telegram.org/bot{config.telegram_bot_token}/sendPhoto"
                )
                tg_resp = await client.post(
                    tg_url,
                    json={
                        "chat_id": config.telegram_chat_id,
                        "caption": caption,
                        "parse_mode": "HTML",
                        "photo": img_url,
                    },
                )
                if tg_resp.is_success:
                    upload_success = True
                else:
                    log.warning(
                        "Telegram Photo failed for birthday: %s %s",
                        tg_resp.status_code,
                        tg_resp.text,
                    )

            if upload_success:
                return True

            # Fallback to text message if photo fails
            tg_url = (
                f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
            )
            tg_resp = await client.post(
                tg_url,
                json={
                    "chat_id": config.telegram_chat_id,
                    "text": caption,
                    "parse_mode": "HTML",
                },
            )
            if not tg_resp.is_success:
                log.error("Birthday notification failed: %s", tg_resp.text)
                return False

            return True

    except Exception:
        log.exception("Exception during birthday notification:")
        return False


async def send_upcoming_schedule_reminder(sch: dict, config) -> bool:
    if not _is_enabled(config):
        return False

    try:
        text = _format_upcoming_schedule_caption(sch)

        async with httpx.AsyncClient(timeout=30.0) as client:
            tg_url = (
                f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
            )
            tg_resp = await client.post(
                tg_url,
                json={
                    "chat_id": config.telegram_chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
            )
            if not tg_resp.is_success:
                log.error("Upcoming schedule reminder failed: %s", tg_resp.text)
                return False

            return True

    except Exception:
        log.exception("Exception during upcoming schedule reminder:")
        return False


async def send_monthly_birthday_list(month_name: str, members: list, config) -> bool:
    if not _is_enabled(config):
        return False

    try:
        if not members:
            return True

        text = _format_monthly_birthday_caption(month_name, members)

        async with httpx.AsyncClient(timeout=30.0) as client:
            tg_url = (
                f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
            )
            tg_resp = await client.post(
                tg_url,
                json={
                    "chat_id": config.telegram_chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
            )
            if not tg_resp.is_success:
                log.error("Monthly birthday list failed: %s", tg_resp.text)
                return False

            return True

    except Exception:
        log.exception("Exception during monthly birthday list:")
        return False


async def send_idn_live_plus_notification(
    payload: dict, config: RecorderConfig
) -> bool:
    """Send a notification to Telegram for new or updated IDN Live Plus schedules."""
    if not _is_enabled(config):
        return False

    log.info("Sending IDN Live Plus schedule Telegram notification")

    screenshot_path = payload.get("screenshot_path")

    caption = _format_idn_live_plus_caption(payload)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            upload_success = False

            if screenshot_path and os.path.exists(screenshot_path):
                log.info("Sending IDN Live Plus notification with Photo")
                tg_url = (
                    f"https://api.telegram.org/bot{config.telegram_bot_token}/sendPhoto"
                )
                try:
                    with open(screenshot_path, "rb") as f:
                        tg_resp = await client.post(
                            tg_url,
                            data={
                                "chat_id": config.telegram_chat_id,
                                "caption": caption,
                                "parse_mode": "HTML",
                            },
                            files={
                                "photo": (
                                    "idn_live_plus.jpg",
                                    f,
                                    "image/jpeg",
                                )
                            },
                        )
                    if tg_resp.is_success:
                        upload_success = True
                    else:
                        log.warning(
                            "Telegram Photo failed: %s %s",
                            tg_resp.status_code,
                            tg_resp.text,
                        )
                except Exception:
                    log.exception("Exception during Photo upload:")

            if upload_success:
                return True

            # Fallback to text message
            tg_url = (
                f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
            )
            tg_resp = await client.post(
                tg_url,
                json={
                    "chat_id": config.telegram_chat_id,
                    "text": caption,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
            )
            if not tg_resp.is_success:
                log.error("IDN Live Plus notification failed: %s", tg_resp.text)
                return False

            return True

    except Exception:
        log.exception("Exception during IDN Live Plus notification:")
        return False


async def send_health_notification(payload: dict, config: RecorderConfig) -> bool:
    """Send a notification to Telegram for health status changes."""
    if not _is_enabled(config):
        return False

    log.info("Sending Health Telegram notification")

    changes = payload.get("changes", [])
    if not changes:
        return True

    text = _format_health_caption(payload)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            tg_url = (
                f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
            )
            tg_resp = await client.post(
                tg_url,
                json={
                    "chat_id": config.telegram_chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
            if not tg_resp.is_success:
                log.error("Health notification failed: %s", tg_resp.text)
                return False

            return True

    except Exception:
        log.exception("Exception during Health notification:")
        return False
