"""Shared notification caption builders.

Every builder returns text with Telegram HTML markup (``<b>``, ``<i>``,
``<a href=...>``). The Telegram notifier sends it verbatim with
``parse_mode="HTML"``; the Page48 notifier converts it to plain text.
Keeping one source of truth means both channels always say the same thing.
"""

import html
import re
import unicodedata
from datetime import datetime, timedelta, timezone

from ..models import LiveInfo

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


def _format_platform_name(platform_str: str) -> str:
    if not platform_str:
        return ""
    if platform_str.lower() == "idn":
        return "IDN"
    return platform_str.title()


def _format_recap_end_live_caption(
    data: dict, live_id: str = "", live_type: str = "public"
) -> str:
    """Format the Telegram caption for recap."""
    member_nickname = html.escape(
        data.get("member_nickname") or data.get("member_name", "Unknown")
    )
    title = data.get("title") or "Siaran Langsung"
    title = html.escape(unicodedata.normalize("NFKC", str(title)).strip())
    raw_platform = str(data.get("platform", ""))
    platform = html.escape(_format_platform_name(raw_platform))

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

    is_showroom = raw_platform.upper() == "SHOWROOM"
    total_idr = _gold_to_idr(total_gold, is_showroom)
    idr_str = f" (~ {_format_rp(total_idr)})" if total_gold > 0 else ""

    caption = f"🎬 Recap Live {platform} {member_nickname}\n\n"
    caption += f"❝<i>{title}</i>❞\n"
    if date_wib_range:
        caption += f"{date_wib_range}\n\n"

    caption += f"<b>Durasi:</b> {duration_str}\n"
    caption += f"<b>Tayangan:</b> {views:,}\n"
    caption += f"<b>Komentar:</b> {chats:,}\n"
    caption += f"<b>Total Gold:</b> {total_gold:,}{idr_str}\n\n"

    top_fans = data.get("top_fans", [])
    paid_fans = [fan for fan in top_fans if fan.get("total_gold", 0) > 0]
    if paid_fans:
        caption += "<b>Top Gifter:</b>\n"
        for i, fan in enumerate(paid_fans[:10], 1):
            name = html.escape(fan.get("user", "Unknown"))
            gold = fan.get("total_gold", 0)
            caption += f"{i}. {name} ({gold:,} gold)\n"

    live_id = live_id or data.get("live_id")
    if live_id:
        history_url = f"https://mypage48.com/jkt48/live/history/live/{live_id}"
        caption += f"\n• <a href='{history_url}'>Data Lengkap di MyPage48</a>"

    youtube_id = data.get("youtube_id")
    if youtube_id and live_type == "public":
        caption += f"\n• <a href='https://youtu.be/{youtube_id}'>Tayangan ulang di YouTube</a>\n"
    else:
        caption += "\n"

    caption += "\n<i>~ MyPage48 ~</i>"

    return caption


def _format_end_live_caption(data: dict) -> str:
    """Format the Telegram caption for simple end live."""
    member_nickname = html.escape(
        data.get("member_nickname") or data.get("member_name", "Unknown")
    )
    platform = html.escape(_format_platform_name(str(data.get("platform", ""))))

    start_at_iso = data.get("start_at", "")
    end_at_iso = data.get("end_at", "")
    date_wib_range = _format_date_range_wib(start_at_iso, end_at_iso)

    title = data.get("title") or "Siaran Langsung"
    title = html.escape(unicodedata.normalize("NFKC", str(title)).strip())

    caption = f"🏁 <b>{member_nickname} telah selesai Live {platform}!</b>\n\n"
    caption += f"❝<i>{title}</i>❞\n\n"
    if date_wib_range:
        caption += f"📅 {date_wib_range}\n\n"

    caption += "<i>~ MyPage48 ~</i>"
    return caption


def _format_replay_live_caption(meta: dict, youtube_title: str, youtube_id: str) -> str:
    """Format the Telegram caption for a newly uploaded YouTube replay."""
    member_nickname = html.escape(
        meta.get("member_nickname") or meta.get("member_name") or "Unknown"
    )
    platform = html.escape(_format_platform_name(meta.get("platform", "")))

    caption = f"▶️ <b>Replay Live {platform} {member_nickname} telah diupload</b>\n\n"
    caption += f"❝<i>{html.escape(youtube_title)}</i>❞\n\n"
    caption += f"• <a href='https://youtu.be/{youtube_id}'>Nonton di YouTube</a>\n"
    caption += f"• <a href='https://mypage48.com/jkt48/live/replay/{youtube_id}'>Nonton di MyPage48</a>\n\n"
    caption += "<i>~ MyPage48 ~</i>"
    return caption


def _format_live_start_caption(live: LiveInfo) -> str:
    """Format the Telegram caption for live start."""
    member_nickname = html.escape(live.member_nickname or live.member_name or "Unknown")
    title = live.title or "Siaran Langsung"
    title = html.escape(unicodedata.normalize("NFKC", str(title)).strip())
    platform = html.escape(_format_platform_name(live.platform))

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

    caption = f"🚀 <b>{member_nickname} sedang Live {platform}!</b>\n"
    caption += f"\n❝<i>{title}</i>❞\n\n"
    if date_wib:
        caption += f"📅 {date_wib}\n\n"

    if app_url:
        caption += f"• <a href='{app_url}'>Nonton di IDN App</a>\n"
        caption += f"• <a href='{official_url}'>Nonton di IDN Web</a>\n\n"
    elif official_url:
        caption += f"• <a href='{official_url}'>Nonton di {platform}</a>\n\n"

    if live.live_type == "public":
        caption += f"• <a href='{watch_url}'>Nonton di MyPage48</a>\n"
        caption += f"• <a href='{multiview_url}'>Nonton via MultiView</a>\n\n"

    caption += "<i>~ MyPage48 ~</i>"
    return caption


def _format_news_caption(news_data: dict) -> str:
    """Format the Telegram caption for new JKT48 news."""
    title = html.escape(news_data.get("title", "Berita JKT48"))
    category = html.escape(news_data.get("category", ""))
    date_iso = news_data.get("valid_date_from", "")
    url = news_data.get("url", "")

    date_wib = _format_date_only_wib(date_iso)

    caption = "📰 <b>Berita Baru JKT48</b>\n\n"
    caption += f"<b>{title}</b>\n\n"
    if date_wib:
        caption += f"📅 {date_wib}\n"
    if category:
        caption += f"🏷 {category}\n"

    caption += f"\n• <a href='{url}'>Baca selengkapnya di jkt48.com</a>\n\n"
    caption += "<i>~ MyPage48 ~</i>"
    return caption


def _format_schedule_summary(sch: dict) -> str:
    title = html.escape(sch.get("title", ""))

    date_str = sch.get("date", "")
    time_str = sch.get("start_time", "")
    if time_str and time_str.count(":") == 2:
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

    bday_members = sch.get("birthday_members", [])
    birthday_str = ""
    if bday_members:
        birthday_str = f"  • 🎂 {', '.join(bday_members)}\n"

    new_tickets = sch.get("new_sales_labels", [])
    new_tickets_str = ""
    if new_tickets:
        sales_periods = sch.get("sales_period", [])
        for nt in new_tickets:
            quotas = []
            for sp in sales_periods:
                if sp.get("label") == nt:
                    for pricing in sp.get("pricing", []):
                        if "quota" in pricing:
                            quotas.append(str(pricing["quota"]))
                    break

            quota_str = ""
            if quotas:
                quota_str = f" - {', '.join(quotas)}"

            new_tickets_str += f"  • 🎟️ Tiket {nt}{quota_str}\n"

    return f"• <b>{title}</b>\n  • {date_wib} {time_str} WIB\n{birthday_str}{new_tickets_str}  • <a href='{url}'>Detail</a>\n\n"


def _format_schedule_caption(payload: dict) -> str:
    """Format the Telegram caption for new or updated schedules."""
    new_count = payload.get("new_count", 0)
    updated_count = payload.get("updated_count", 0)

    caption = ""
    new_schedules = payload.get("new_schedules", [])
    updated_schedules = payload.get("updated_schedules", [])

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
    return caption


def _format_idn_live_plus_summary(sch: dict) -> str:
    title = sch.get("title", "")
    # Remove trailing date suffix like ' - 2026/07/16'
    title = re.sub(r"\s*-\s*\d{4}/\d{2}/\d{2}$", "", title).strip() or title
    scheduled_at = sch.get("scheduled_at", "")
    live_id = sch.get("live_id", "")

    date_wib = _format_date_wib(scheduled_at) if scheduled_at else ""
    preview_url = f"https://www.idn.app/jkt48-official/live/preview/{live_id}"

    safe_title = html.escape(title)
    return f"• <b>{safe_title}</b>\n  • {date_wib}\n  • <a href='{preview_url}'>Detail</a>\n\n"


def _format_idn_live_plus_caption(payload: dict) -> str:
    """Format the Telegram caption for new or updated IDN Live Plus schedules."""
    new_count = payload.get("new_count", 0)
    updated_count = payload.get("updated_count", 0)

    caption = ""
    new_schedules = payload.get("new_schedules", [])
    updated_schedules = payload.get("updated_schedules", [])

    if new_schedules:
        caption += (
            f"<b>📺 Berikut {new_count} jadwal IDN Live Plus yang akan datang</b>\n\n"
        )
        for sch in new_schedules:
            caption += _format_idn_live_plus_summary(sch)

    if updated_schedules:
        all_types = set()
        for sch in updated_schedules:
            all_types.update(sch.get("update_types", []))

        types_str = " & ".join(sorted(all_types))
        caption += (
            f"<b>🔄 Terdapat {updated_count} jadwal dengan update {types_str}</b>\n\n"
        )
        for sch in updated_schedules:
            caption += _format_idn_live_plus_summary(sch)

    caption += "<i>~ MyPage48 ~</i>"
    return caption


def _format_daily_schedule_caption(payload: dict) -> str:
    """Format the daily reminder caption of today's schedules."""
    schedules = payload.get("schedules", [])

    count = len(schedules)
    caption = f"☀️Selamat siang, hari ini ada {count} jadwal~\n\n"

    for sch in schedules:
        title = sch.get("title", "")
        if sch.get("type") == "SHOW" and sch.get("jkt48_member_type"):
            title += f" ({sch.get('jkt48_member_type')})"
        title = html.escape(title)

        date_str = sch.get("date", "")
        time_str = sch.get("start_time", "")
        if time_str and time_str.count(":") == 2:
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
        bday_members = sch.get("birthday_members", [])

        entry = f"• <b>{title}</b>"
        entry += f"\n  • {date_wib} {time_str} WIB"
        if bday_members:
            entry += f"\n  • 🎂 {', '.join(bday_members)}"

        if members:
            entry += f"\n  • {len(members)} Member"
            for m in members:
                safe_m = html.escape(m)
                entry += f"\n    • {safe_m}"

        entry += f"\n  • <a href='{url}'>Detail</a>\n\n"
        caption += entry

    caption += "<i>~ MyPage48 ~</i>"
    return caption


def _format_birthday_caption(member: dict) -> str:
    name = html.escape(member.get("name", "Member"))
    age = member.get("age", "?")

    return f"🎂 Selamat ulang tahun {name} yang ke {age}\n\n<i>~ MyPage48 ~</i>"


def _format_upcoming_schedule_caption(sch: dict) -> str:
    title = html.escape(sch.get("title", ""))
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
        return f"Selamat {greeting}! Sudah siapkah untuk menyaksikan pertunjukan {title} oleh {team_name}?\n\n<i>~ MyPage48 ~</i>"

    return f"Selamat {greeting}! Sudah siapkah untuk mengikuti {title}?\n\n<i>~ MyPage48 ~</i>"


def _format_monthly_birthday_caption(month_name: str, members: list) -> str:
    text = f"🎉 <b>Daftar Ulang Tahun Member JKT48 Bulan {month_name.capitalize()}</b> 🎉\n\n"

    for m in members:
        b_date = m.get("birthdate", "")
        name = html.escape(m.get("name", ""))
        age = m.get("new_age", "")
        text += f"• {name} - {b_date} ({age} Tahun)\n"

    text += "\n<i>~ MyPage48 ~</i>"
    return text


def _format_health_caption(payload: dict) -> str:
    """Format the health status change caption."""
    changes = payload.get("changes", [])
    state = payload.get("state", {})
    if not state:
        # Fallback if state is not in payload for some reason
        state = {c.get("service"): c.get("new_state") for c in changes}

    services = [
        ("frontend", "Web"),
        ("api", "API"),
        ("database", "Database"),
        ("storage", "Image Storage"),
    ]

    is_any_down = any(state.get(k) == "DOWN" for k, _ in services)

    if is_any_down:
        text = "🔴 <b>Monitoring Alert</b>\n\n"
        text += "Mohon maaf <a href='https://mypage48.com'>MyPage48.com</a> sedang mengalami kendala, saat ini web tidak dapat diakses untuk sementara waktu.\n"
    else:
        text = "🟢 <b>Monitoring Alert</b>\n\n"
        text += "<a href='https://mypage48.com'>MyPage48.com</a> kembali beroperasi dengan normal.\n"

    text += "\n<i>~ MyPage48 ~</i>"
    return text
