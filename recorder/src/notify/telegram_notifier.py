import logging
import os
import unicodedata
from datetime import datetime, timedelta, timezone

import httpx

from ..config import RecorderConfig
from ..models import LiveInfo

log = logging.getLogger("notify")


def _format_date_wib(iso_string: str) -> str:
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        wib_tz = timezone(timedelta(hours=7))
        dt_wib = dt.astimezone(wib_tz)

        months = [
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
        day = dt_wib.day
        month = months[dt_wib.month]
        year = dt_wib.year
        time_str = dt_wib.strftime("%H:%M")

        return f"{day} {month} {year}, {time_str} WIB"
    except Exception:
        return iso_string


def _format_date_range_wib(start_iso: str, duration_s: int) -> str:
    if not start_iso:
        return ""
    try:
        dt_start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        wib_tz = timezone(timedelta(hours=7))
        dt_wib_start = dt_start.astimezone(wib_tz)
        dt_wib_end = dt_wib_start + timedelta(seconds=duration_s)

        months = [
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

        start_day = dt_wib_start.day
        start_month = months[dt_wib_start.month]
        start_year = dt_wib_start.year
        start_time = dt_wib_start.strftime("%H:%M")

        end_day = dt_wib_end.day
        end_month = months[dt_wib_end.month]
        end_year = dt_wib_end.year
        end_time = dt_wib_end.strftime("%H:%M")

        if start_day == end_day and start_month == end_month and start_year == end_year:
            return (
                f"{start_day} {start_month} {start_year}, {start_time} - {end_time} WIB"
            )
        else:
            return f"{start_day} {start_month} {start_year}, {start_time} - {end_day} {end_month} {end_year}, {end_time} WIB"
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
    date_wib_range = _format_date_range_wib(start_at_iso, duration_s)

    # Stats
    views = data.get("view_num", 0)
    chats = data.get("total_chats", 0)
    total_gold = data.get("total_gold", 0)

    is_showroom = platform == "SHOWROOM"
    total_idr = _gold_to_idr(total_gold, is_showroom)
    idr_str = f" (~ {_format_rp(total_idr)})" if total_gold > 0 else ""

    caption = f"🔚 <b>{member_nickname} telah selesai LIVE {platform}!</b>\n"
    if date_wib_range:
        caption += f"📅 {date_wib_range}\n"

    caption += f"\nArsip Live: {member_nickname} ({platform})\n"
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
            fan_idr = _gold_to_idr(gold, is_showroom)
            fan_idr_str = f" (~ {_format_rp(fan_idr)})" if gold > 0 else ""
            caption += f"{i}. {name} (<b>{gold:,} gold</b>{fan_idr_str})\n"

    live_id = live_id or data.get("live_id")
    if live_id:
        history_url = f"https://mypage48.com/jkt48/live/history/live/{live_id}"
        caption += f"\n<a href='{history_url}'>Data Lengkap di MyPage48</a>"

    youtube_id = data.get("youtube_id")
    if youtube_id:
        caption += (
            f"\n<a href='https://youtu.be/{youtube_id}'>Tayangan ulang di YouTube</a>\n"
        )
    else:
        caption += "\n"

    caption += "\n<i>~ MyPage48 ~</i>"

    return caption


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

            # 1. Add cover image first
            thumbnail_path = ""
            if folder_path:
                yt_thumb = os.path.join(folder_path, f"{live_id}_yt_thumb.jpg")
                if os.path.exists(yt_thumb):
                    thumbnail_path = yt_thumb
                else:
                    thumbnail_path = os.path.join(folder_path, f"{live_id}.jpg")

            if thumbnail_path and os.path.exists(thumbnail_path):
                images_to_send.append(("cover", thumbnail_path))

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
                            if len(images_to_send) >= 4:
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
                except Exception as e:
                    for _, f, _ in files.values():
                        if not f.closed:
                            f.close()
                    log.warning("Exception during MediaGroup upload: %s", e)

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
                except Exception as e:
                    log.warning("Exception during Photo upload: %s", e)

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

    except Exception as e:
        log.error("Exception during Telegram notification for %s: %s", live_id, e)
        return False


async def send_live_start_notification(live: LiveInfo, config: RecorderConfig) -> bool:
    """Send a notification to Telegram when a live stream starts."""
    if not config.telegram_bot_token or not config.telegram_chat_id:
        return False

    log.info("Sending live start Telegram notification for %s", live.live_id)

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
        caption += f"<a href='{app_url}'>Nonton di IDN App</a>\n"
        caption += f"<a href='{official_url}'>Nonton di IDN Web</a>\n\n"
    elif official_url:
        caption += f"<a href='{official_url}'>Nonton di {platform}</a>\n\n"
    caption += f"<a href='{watch_url}'>Nonton di MyPage48</a>\n"
    caption += f"<a href='{multiview_url}'>Nonton via MultiView</a>\n\n"

    caption += "<i>~ MyPage48 ~</i>"

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
    except Exception as e:
        log.error("Exception during live start notification: %s", e)
        return False
