import logging
import math
import os
import unicodedata
from datetime import datetime, timedelta, timezone

import httpx
from PIL import Image

from ..config import RecorderConfig
from ..models import LiveInfo
from .web_screenshot import capture_web_screenshot

log = logging.getLogger("notify")

LIVE_DETAIL_BASE_URL = "https://mypage48.com/jkt48/live/history/live"

ID_MONTHS = [
    "",
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
]
ID_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
WIB_TZ = timezone(timedelta(hours=7))


def _format_date_wib(iso_string: str) -> str:
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        dt_wib = dt.astimezone(WIB_TZ)

        day_name = ID_DAYS[dt_wib.weekday()]

        day = dt_wib.day
        month = ID_MONTHS[dt_wib.month]
        year = dt_wib.year
        time_str = dt_wib.strftime("%H:%M")

        return f"{day_name}, {day} {month} {year}, {time_str} WIB"
    except Exception:
        return iso_string


def _format_date_only_wib(iso_string: str) -> str:
    """Format only the date part, assuming the string is already in WIB despite having 'Z'."""
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        dt_wib = dt.astimezone(WIB_TZ)

        day_name = ID_DAYS[dt_wib.weekday()]
        day = dt_wib.day
        month = ID_MONTHS[dt_wib.month]
        year = dt_wib.year

        return f"{day_name}, {day} {month} {year}"
    except Exception:
        return iso_string


def _format_date_range_wib(start_iso: str, end_iso: str) -> str:
    if not start_iso:
        return ""
    try:
        dt_start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        dt_wib_start = dt_start.astimezone(WIB_TZ)

        if end_iso:
            dt_end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
            dt_wib_end = dt_end.astimezone(WIB_TZ)
        else:
            dt_wib_end = dt_wib_start

        start_day_name = ID_DAYS[dt_wib_start.weekday()]
        start_day = dt_wib_start.day
        start_month = ID_MONTHS[dt_wib_start.month]
        start_year = dt_wib_start.year
        start_time = dt_wib_start.strftime("%H:%M")

        end_day_name = ID_DAYS[dt_wib_end.weekday()]
        end_day = dt_wib_end.day
        end_month = ID_MONTHS[dt_wib_end.month]
        end_year = dt_wib_end.year
        end_time = dt_wib_end.strftime("%H:%M")

        if start_day == end_day and start_month == end_month and start_year == end_year:
            return f"{start_day_name}, {start_day} {start_month} {start_year}, {start_time} - {end_time} WIB"
        else:
            return f"{start_day_name}, {start_day} {start_month} {start_year}, {start_time} - {end_day_name}, {end_day} {end_month} {end_year}, {end_time} WIB"
    except Exception:
        return start_iso


def _gold_to_idr(gold: int, is_showroom: bool) -> float:
    return gold * 111.5 if is_showroom else (gold * 7500) / 3


def _format_rp(amount: float) -> str:
    s = f"{int(amount):,}".replace(",", ".")
    return f"Rp {s}"


def _format_end_live_caption(data: dict, live_id: str = "") -> str:
    """Format the Telegram caption."""
    member_nickname = data.get("member_nickname") or data.get("member_name", "Unknown")
    title = data.get("title") or "Siaran Langsung"
    title = unicodedata.normalize("NFKC", str(title)).strip()
    platform = str(data.get("platform", "")).upper()

    # Format duration
    duration_s = data.get("duration", 0)
    h, rem = divmod(duration_s, 3600)
    m, s = divmod(rem, 60)
    if h:
        duration_str = f"{h}j {m}m {s}d"
    elif m:
        duration_str = f"{m}m {s}d"
    else:
        duration_str = f"{s}d"

    start_at_iso = data.get("start_at", "")
    end_at_iso = data.get("end_at", "")
    date_wib_range = _format_date_range_wib(start_at_iso, end_at_iso)

    # Stats
    views = data.get("view_num", 0)
    chats = data.get("total_chats", 0)
    total_gold = data.get("total_gold", 0)

    is_showroom = platform == "SHOWROOM"
    total_idr = _gold_to_idr(total_gold, is_showroom)
    idr_str = f" (~ {_format_rp(total_idr)})" if total_gold > 0 else ""

    caption = f"🔚 <b>{member_nickname} telah selesai LIVE {platform}!</b>\n"
    if date_wib_range:
        caption += f"📅 {date_wib_range}\n\n"

    caption += f"❝<i>{title}</i>❞\n\n"

    caption += f"<b>Durasi:</b> {duration_str}\n"
    caption += f"<b>Tayangan:</b> {views:,}\n"
    caption += f"<b>Komentar:</b> {chats:,}\n"
    caption += f"<b>Total Gold:</b> {total_gold:,}{idr_str}\n\n"

    top_fans = data.get("top_fans", [])
    paid_fans = [fan for fan in top_fans if fan.get("total_gold", 0) > 0]
    if paid_fans:
        caption += "<b>Top Gifter:</b>\n"
        for i, fan in enumerate(paid_fans[:10], 1):
            name = fan.get("user", "Unknown")
            gold = fan.get("total_gold", 0)
            caption += f"{i}. {name} ({gold:,} gold)\n"

    live_id = live_id or data.get("live_id")
    if live_id:
        history_url = f"https://mypage48.com/jkt48/live/history/live/{live_id}"
        caption += f"\n• <a href='{history_url}'>Data Lengkap di MyPage48</a>"

    youtube_id = data.get("youtube_id")
    if youtube_id:
        caption += f"\n• <a href='https://youtu.be/{youtube_id}'>Tayangan ulang di YouTube</a>\n"
    else:
        caption += "\n"

    caption += "\n<i>~ MyPage48 ~</i>"

    return caption


def _process_and_split_image(image_path: str, max_height: int = 8000) -> list[str]:
    """Check if image exceeds max_height, and if so, split it into multiple images."""
    try:
        # Increase max pixels limit for large web screenshots
        Image.MAX_IMAGE_PIXELS = None

        with Image.open(image_path) as img:
            width, height = img.size
            if height <= max_height:
                return [image_path]

            num_parts = math.ceil(height / max_height)
            part_height = math.ceil(height / num_parts)

            split_paths = []
            base_name, ext = os.path.splitext(image_path)

            for i in range(num_parts):
                top = i * part_height
                bottom = min((i + 1) * part_height, height)

                part_img = img.crop((0, top, width, bottom))
                part_path = f"{base_name}_part{i+1}{ext}"

                # Convert RGBA to RGB if saving as JPEG to avoid error
                if part_img.mode in ("RGBA", "P") and ext.lower() in (".jpg", ".jpeg"):
                    part_img = part_img.convert("RGB")

                part_img.save(part_path)
                split_paths.append(part_path)

            return split_paths
    except Exception as e:
        log.warning("Failed to process/split image %s: %s", image_path, e)
        return [image_path]


async def send_end_live_notification(
    live_id: str, config: RecorderConfig, folder_path: str = ""
) -> bool:
    """Fetch replay data and send a notification to Telegram."""
    if not config.telegram_bot_token or not config.telegram_chat_id:
        log.info("Telegram not configured (bot token or chat ID missing). Skipping.")
        return False

    api_url = f"{config.api_base_url.rstrip('/')}/replays/{live_id}"
    log.info("Fetching replay data for Telegram notification from %s", api_url)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(api_url)

            if not resp.is_success:
                log.error(
                    "Failed to fetch replay data: %s %s", resp.status_code, resp.text
                )
                return False

            data = resp.json()
            caption = _format_end_live_caption(data, live_id=live_id)

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


def _format_live_start_caption(live: LiveInfo) -> str:
    """Format the Telegram caption for live start."""
    member_nickname = live.member_nickname or live.member_name or "Unknown"
    title = live.title or "Siaran Langsung"
    title = unicodedata.normalize("NFKC", str(title)).strip()
    platform = live.platform.upper()

    start_at_iso = live.start_at
    date_wib = _format_date_wib(start_at_iso)

    identifier = live.live_id if live.platform.lower() == "idn" else live.room_id
    watch_url = f"https://mypage48.com/jkt48/live/{live.platform.lower()}/{identifier}"
    multiview_url = "https://mypage48.com/jkt48/live/multiview"

    app_url = ""
    if live.platform.lower() == "idn":
        url_key = live.room_url_key or live.room_identifier or "jkt48"
        official_url = f"https://www.idn.app/{url_key}/live/{live.live_id}"
        app_url = f"https://click.idn.media/VKUf?af_dp=idnapp://live/{url_key}/?room={live.live_id}&af_web_dp={official_url}&c=detail-liveroom&deep_link_value=idnapp://live/?room={live.live_id}&pid=idnapp"
    elif live.platform.lower() == "showroom":
        url_key = live.room_url_key or live.room_identifier or live.room_id
        official_url = f"https://www.showroom-live.com/r/{url_key}"
    else:
        official_url = ""

    caption = f"🔴 <b>{member_nickname} sedang LIVE {platform}!</b>\n"
    if date_wib:
        caption += f"📅 {date_wib}\n"
    caption += f"\n❝<i>{title}</i>❞\n\n"

    if app_url:
        caption += f"• <a href='{app_url}'>Nonton di IDN App</a>\n"
        caption += f"• <a href='{official_url}'>Nonton di IDN Web</a>\n\n"
    elif official_url:
        caption += f"• <a href='{official_url}'>Nonton di {platform}</a>\n\n"
    caption += f"• <a href='{watch_url}'>Nonton di MyPage48</a>\n"
    caption += f"• <a href='{multiview_url}'>Nonton via MultiView</a>\n\n"

    caption += "<i>~ MyPage48 ~</i>"
    return caption


async def send_live_start_notification(live: LiveInfo, config: RecorderConfig) -> bool:
    """Send a notification to Telegram when a live stream starts."""
    if not config.telegram_bot_token or not config.telegram_chat_id:
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
    if not config.telegram_bot_token or not config.telegram_chat_id:
        return False

    log.info("Sending news Telegram notification for %s", news_data.get("news_id"))

    title = news_data.get("title", "Berita JKT48")
    category = news_data.get("category", "")
    date_iso = news_data.get("valid_date_from", "")
    url = news_data.get("url", "")
    screenshot_path = news_data.get("screenshot_path")
    article_images = news_data.get("article_images", [])

    # Format the date using the new function that only shows the date
    date_wib = _format_date_only_wib(date_iso)

    caption = f"📰 <b>Berita Baru JKT48</b>\n\n"
    caption += f"<b>{title}</b>\n\n"
    if date_wib:
        caption += f"📅 {date_wib}\n"
    if category:
        caption += f"🏷 {category}\n"

    caption += f"\n• <a href='{url}'>Baca selengkapnya di jkt48.com</a>\n\n"
    caption += "<i>~ MyPage48 ~</i>"

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
    if not config.telegram_bot_token or not config.telegram_chat_id:
        return False

    log.info("Sending schedule Telegram notification")

    new_count = payload.get("new_count", 0)
    updated_count = payload.get("updated_count", 0)
    screenshot_path = payload.get("screenshot_path")

    caption = ""
    new_schedules = payload.get("new_schedules", [])
    updated_schedules = payload.get("updated_schedules", [])

    def _format_schedule_summary(sch):
        title = sch.get("title", "")

        date_str = sch.get("date", "")
        time_str = sch.get("start_time", "")
        if time_str.count(":") == 2:
            time_str = ":".join(time_str.split(":")[:2])
        try:
            date_wib = _format_date_only_wib(f"{date_str}T00:00:00Z")
        except Exception:
            date_wib = date_str

        sch_id = sch.get("id", "")
        ref_code = sch.get("reference_code", "")
        sch_type = sch.get("type", "")

        if ref_code:
            if sch_type == "SHOW":
                url = f"https://jkt48.com/purchase/schedule/show?code={ref_code}"
            elif sch_type == "EVENT":
                url = f"https://jkt48.com/purchase/schedule/event?code={ref_code}"
            elif sch_type == "EXCLUSIVE":
                url = f"https://jkt48.com/purchase/exclusive?code={ref_code}"
            else:
                url = f"https://jkt48.com/theater/schedule?id={sch_id}&lang=id"
        else:
            url = f"https://jkt48.com/theater/schedule?id={sch_id}&lang=id"

        return f"• <b>{title}</b>\n  • {date_wib} {time_str} WIB\n  • <a href='{url}'>Detail</a>\n\n"

    if new_schedules:
        caption += f"<b>🆕 Berikut {new_count} jadwal yang akan datang</b>\n\n"
        for sch in new_schedules:
            caption += _format_schedule_summary(sch)

    if updated_schedules:
        all_types = set()
        for sch in updated_schedules:
            all_types.update(sch.get("update_types", ["MEMBER"]))

        if "MEMBER" in all_types and "TIKET" in all_types:
            types_str = "lineup & tiket"
        elif "TIKET" in all_types:
            types_str = "tiket"
        else:
            types_str = "lineup"

        caption += (
            f"<b>🔄 Terdapat {updated_count} jadwal dengan update {types_str}</b>\n\n"
        )
        for sch in updated_schedules:
            caption += _format_schedule_summary(sch)

    caption += "• <a href='https://jkt48.com/theater/schedule'>Cek selengkapnya di jkt48.com</a>\n\n"
    caption += "<i>~ MyPage48 ~</i>"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            upload_success = False

            if screenshot_path and os.path.exists(screenshot_path):
                log.info("Sending schedule notification with Photo")
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
    schedules = payload.get("schedules", [])
    if not schedules:
        return True

    count = len(schedules)
    caption = f"☀️Selamat siang, hari ini ada {count} jadwal~\n\n"

    for sch in schedules:
        title = sch.get("title", "")
        if sch.get("type") == "SHOW" and sch.get("jkt48_member_type"):
            title += f" ({sch.get('jkt48_member_type')})"

        date_str = sch.get("date", "")
        time_str = sch.get("start_time", "")
        if time_str.count(":") == 2:
            time_str = ":".join(time_str.split(":")[:2])

        try:
            date_wib = _format_date_only_wib(f"{date_str}T00:00:00Z")
        except Exception:
            date_wib = date_str

        sch_id = sch.get("id", "")
        ref_code = sch.get("reference_code", "")
        sch_type = sch.get("type", "")

        if ref_code:
            if sch_type == "SHOW":
                url = f"https://jkt48.com/purchase/schedule/show?code={ref_code}"
            elif sch_type == "EVENT":
                url = f"https://jkt48.com/purchase/schedule/event?code={ref_code}"
            elif sch_type == "EXCLUSIVE":
                url = f"https://jkt48.com/purchase/exclusive?code={ref_code}"
            else:
                url = f"https://jkt48.com/theater/schedule?id={sch_id}&lang=id"
        else:
            url = f"https://jkt48.com/theater/schedule?id={sch_id}&lang=id"

        members = sch.get("members", [])

        entry = f"• <b>{title}</b>"
        entry += f"\n  • {date_wib} {time_str} WIB"

        if members:
            entry += f"\n  • {len(members)} Member"
            for m in members:
                entry += f"\n    • {m}"

        entry += f"\n  • <a href='{url}'>Detail</a>\n\n"
        caption += entry

    caption += "<i>~ MyPage48 ~</i>"

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
    name = member.get("name", "Member")
    age = member.get("age", "?")
    img_url = member.get("img", "")

    caption = f"🎂 Selamat ulang tahun {name} yang ke {age}\n\n<i>~ MyPage48 ~</i>"

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
    try:
        title = sch.get("title", "")
        sch_type = sch.get("type", "")
        member_type = sch.get("jkt48_member_type", "")
        start_time_str = sch.get("start_time", "00:00:00")

        # Parse hour for greeting
        try:
            hour = int(start_time_str.split(":")[0])
        except Exception:
            hour = 12

        if 0 <= hour < 11:
            greeting = "pagi"
        elif 11 <= hour < 15:
            greeting = "siang"
        elif 15 <= hour < 18:
            greeting = "sore"
        else:
            greeting = "malam"

        if sch_type == "SHOW":
            m_type_up = member_type.upper()
            if m_type_up == "TRAINEE":
                team_name = "JKT48 Trainee"
            elif m_type_up == "JKT48":
                team_name = "JKT48"
            else:
                team_name = f"Team {m_type_up} JKT48"
            text = f"Selamat {greeting}! Sudah siapkah untuk menyaksikan pertunjukan {title} oleh {team_name}?\n\n<i>~ MyPage48 ~</i>"
        else:
            text = f"Selamat {greeting}! Sudah siapkah untuk mengikuti {title}?\n\n<i>~ MyPage48 ~</i>"

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
    try:
        if not members:
            return True

        text = f"🎉 <b>Daftar Ulang Tahun Member JKT48 Bulan {month_name.capitalize()}</b> 🎉\n\n"

        for m in members:
            b_date = m.get("birthdate", "")
            name = m.get("name", "")
            age = m.get("new_age", "")
            text += f"• {name} - {b_date} ({age} Tahun)\n"

        text += "\n<i>~ MyPage48 ~</i>"

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
