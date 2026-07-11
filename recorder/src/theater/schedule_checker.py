import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone

import httpx

from ..config import RecorderConfig
from ..notify.telegram_notifier import (
    _format_date_only_wib,
    send_daily_schedule_reminder,
)
from .html_screenshot import capture_html_screenshot


class ScheduleChecker:
    def __init__(self, config: RecorderConfig):
        self.config = config
        self.log = logging.getLogger("theater")
        self.theater_dir = self.config.theater_dir
        self.state_file = os.path.join(self.theater_dir, "last_schedules_state.json")
        self.pending_dir = os.path.join(self.theater_dir, "pending_notifications")

        os.makedirs(self.theater_dir, exist_ok=True)
        os.makedirs(self.pending_dir, exist_ok=True)

    def _get_schedule_state(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_schedule_state(self, state: dict):
        with open(self.state_file, "w") as f:
            json.dump(state, f)

    async def _fetch_detail(
        self, client: httpx.AsyncClient, ref_code: str
    ) -> tuple[list[str] | None, list[dict] | None]:
        detail_url = f"https://jkt48.com/api/v1/theater-shows/{ref_code}?lang=id"
        try:
            resp = await client.get(detail_url, timeout=10.0)
            if resp.is_success:
                data = resp.json().get("data", {})
                members_data = data.get("jkt48_member", [])
                sales_period = data.get("sales_period", [])
                members = []
                for m in members_data:
                    if isinstance(m, dict):
                        members.append(m.get("name", "Unknown"))
                    elif isinstance(m, str):
                        members.append(m)
                return sorted(members), sales_period
            else:
                self.log.warning(
                    "Failed to fetch schedule detail %s: HTTP %s",
                    ref_code,
                    resp.status_code,
                )
                return None, None
        except Exception as e:
            self.log.warning("Exception fetching schedule detail %s: %s", ref_code, e)
        return None, None

    async def _check_schedules(self):
        self.log.info("Checking JKT48 schedules...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://jkt48.com/theater/schedule",
            "Origin": "https://jkt48.com",
        }

        # Use real-time WIB date
        today_wib = datetime.now(timezone(timedelta(hours=7)))

        months_to_check = [(today_wib.month, today_wib.year)]

        next_month = today_wib.month + 1
        next_year = today_wib.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        months_to_check.append((next_month, next_year))

        current_state = self._get_schedule_state()
        new_state = dict(current_state)

        new_schedules = []
        updated_schedules = []

        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                for month, year in months_to_check:
                    url = f"https://jkt48.com/api/v1/schedules?lang=id&month={month}&year={year}"
                    resp = await client.get(url)
                    if not resp.is_success:
                        self.log.warning(
                            "Failed to fetch schedules for %02d-%04d: %s",
                            month,
                            year,
                            resp.status_code,
                        )
                        continue

                    data = resp.json()
                    schedules = data.get("data", [])

                    for sch in schedules:
                        sch_id = str(sch.get("schedule_id"))
                        if not sch_id:
                            continue

                        sch_date_str = sch.get("date", "")
                        try:
                            sch_date = datetime.strptime(
                                sch_date_str, "%Y-%m-%d"
                            ).date()
                            if sch_date < today_wib.date():
                                continue
                        except Exception:
                            pass

                        members = []
                        sales_period = []
                        if sch.get("type") == "SHOW" and sch.get("reference_code"):
                            fetched_members, fetched_sales = await self._fetch_detail(
                                client, sch.get("reference_code")
                            )
                            if fetched_members is None:
                                if sch_id in current_state:
                                    members = current_state[sch_id].get("members", [])
                                    sales_period = current_state[sch_id].get(
                                        "sales_period", []
                                    )
                            else:
                                members = fetched_members
                                sales_period = fetched_sales

                        sch_data = {
                            "title": sch.get("title", ""),
                            "date": sch.get("date", ""),
                            "start_time": sch.get("start_time", ""),
                            "type": sch.get("type", ""),
                            "jkt48_member_type": sch.get("jkt48_member_type", ""),
                            "members": members,
                            "sales_period": sales_period,
                            "id": sch_id,
                            "link": sch.get("link", ""),
                            "reference_code": sch.get("reference_code", ""),
                        }

                        if sch_id not in current_state:
                            new_schedules.append(sch_data)
                            new_state[sch_id] = {
                                "members": members,
                                "sales_period": sales_period,
                            }
                        else:
                            old_members = current_state[sch_id].get("members", [])
                            old_sales = current_state[sch_id].get("sales_period", [])

                            update_types = []
                            if members != old_members:
                                update_types.append("MEMBER")
                            if sales_period != old_sales:
                                update_types.append("TIKET")

                            if update_types:
                                sch_data["update_types"] = update_types
                                updated_schedules.append(sch_data)

                            new_state[sch_id] = {
                                "members": members,
                                "sales_period": sales_period,
                            }

                if new_schedules or updated_schedules:
                    self.log.info(
                        "Found %d new schedules and %d updated schedules.",
                        len(new_schedules),
                        len(updated_schedules),
                    )

                    all_schedules = [("new", s) for s in new_schedules] + [
                        ("updated", s) for s in updated_schedules
                    ]
                    chunk_size = 5

                    for i in range(0, len(all_schedules), chunk_size):
                        chunk = all_schedules[i : i + chunk_size]
                        chunk_new = [s[1] for s in chunk if s[0] == "new"]
                        chunk_updated = [s[1] for s in chunk if s[0] == "updated"]

                        await self._generate_and_send_notification(
                            chunk_new, chunk_updated
                        )
                        await asyncio.sleep(1.5)

                    self._save_schedule_state(new_state)
                else:
                    self.log.debug("No new schedules or updates found.")

        except Exception:
            self.log.exception("Exception during schedule check:")

    async def _generate_and_send_notification(self, new_schedules, updated_schedules):
        timestamp_ms = int(time.time() * 1000)
        screenshot_path = os.path.join(self.pending_dir, f"schedule_{timestamp_ms}.jpg")

        html_content = self._generate_html(new_schedules, updated_schedules)

        success = await capture_html_screenshot(
            html_content, screenshot_path, wait_ms=1000
        )

        payload = {
            "type": "schedule",
            "new_count": len(new_schedules),
            "updated_count": len(updated_schedules),
            "screenshot_path": screenshot_path if success else None,
            "timestamp": timestamp_ms,
            "new_schedules": new_schedules,
            "updated_schedules": updated_schedules,
        }

        payload_file = os.path.join(self.pending_dir, f"schedule_{timestamp_ms}.json")
        with open(payload_file, "w") as f:
            json.dump(payload, f, indent=2)

        self.log.info(
            "Successfully prepared schedule notification payload: %s", payload_file
        )

    def _generate_html(
        self, new_schedules, updated_schedules, is_reminder=False
    ) -> str:
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

        def format_ticket_date(iso_str):
            if not iso_str:
                return ""
            try:
                dt = datetime.fromisoformat(iso_str)
                return f"{dt.day} {ID_MONTHS[dt.month]} {dt.year}, {dt.strftime('%H.%M')} WIB"
            except Exception:
                return iso_str

        def render_schedule(sch, is_update=False, is_reminder=False):
            if is_reminder:
                badge_text = "HARI INI"
                badge_html = f"<span class='update-badge' style='background:#ef4444;color:white;'>{badge_text}</span>"
            elif is_update:
                types = sch.get("update_types", ["MEMBER"])
                types_str = " & ".join(types)
                badge_text = f"UPDATE {types_str}"
                badge_html = f"<span class='update-badge'>{badge_text}</span>"
            else:
                badge_text = "BARU"
                badge_html = f"<span class='update-badge'>{badge_text}</span>"
                types = sch.get("update_types", ["MEMBER"])
                types_str = " & ".join(types)
                badge_text = f"UPDATE {types_str}"

            date_str = sch["date"]
            try:
                date_wib = _format_date_only_wib(f"{date_str}T00:00:00Z")
            except Exception:
                date_wib = date_str

            time_str = sch["start_time"]
            if time_str.count(":") == 2:
                time_str = ":".join(time_str.split(":")[:2])

            title_text = sch["title"]
            if sch.get("type") == "SHOW" and sch.get("jkt48_member_type"):
                title_text += f" ({sch['jkt48_member_type']})"

            members_html = ""
            if sch["members"]:
                members_badges = "".join(
                    f'<span class="member-badge">{m}</span>' for m in sch["members"]
                )
                members_html = f"<div class='section-title'>Anggota yang tampil:</div><div class='member-list'>{members_badges}</div>"
            else:
                if sch["type"] == "SHOW":
                    members_html = f"<div class='section-title'>Anggota yang tampil:</div><div class='member-list'><span class='member-badge' style='background:#f3f4f6;color:#6b7280;border-color:#e5e7eb;'>Akan segera diumumkan</span></div>"

            sales_html = ""
            if sch["sales_period"]:
                sales_html = "<div class='section-title'>Periode Penjualan Tiket:</div><ul class='ticket-list'>"
                for sp in sch["sales_period"]:
                    lbl = sp.get("label", "")
                    start_d = format_ticket_date(sp.get("start_date", ""))
                    end_d = format_ticket_date(sp.get("end_date", ""))

                    quotas = []
                    for pricing in sp.get("pricing", []):
                        if "quota" in pricing:
                            quotas.append(
                                f"{pricing['quota']} {pricing.get('label', '')}".strip()
                            )

                    quota_html = ""
                    if quotas:
                        quota_html = f"<div style='margin-bottom: 2px; color: #4b5563;'>Quota: {', '.join(quotas)}</div>"

                    sales_html += f"<li><strong>{lbl}</strong>{quota_html}<div style='color: #6b7280;'>{start_d} - {end_d}</div></li>"
                sales_html += "</ul>"

            return f"""
                <div class="schedule-card">
                    <div class="schedule-header">
                        <span class="schedule-title">{title_text}</span>
                        {badge_html}
                    </div>
                    <div class="schedule-time">📅 {date_wib} &bull; ⏰ {time_str} WIB</div>
                    {members_html}
                    {sales_html}
                </div>
            """

        # Use real-time WIB date
        today_wib = datetime.now(timezone(timedelta(hours=7)))
        today_str = _format_date_only_wib(today_wib.isoformat())

        content_html = ""

        if new_schedules:
            for sch in new_schedules:
                content_html += render_schedule(
                    sch, is_update=False, is_reminder=is_reminder
                )

        if updated_schedules:
            for sch in updated_schedules:
                content_html += render_schedule(
                    sch, is_update=True, is_reminder=is_reminder
                )

        content_html += (
            "<div class='footer'>Mohon dukungannya selalu untuk JKT48.</div>"
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
        <style>
            html {{ background-color: #fcfcfc; }}
            body {{ 
                font-family: 'Inter', -apple-system, sans-serif; 
                padding: 40px; 
                background-color: #fcfcfc; 
                color: #1f2937; 
                line-height: 1.5; 
                max-width: 800px; 
                margin: 0 auto;
            }}
            h1 {{ color: #111827; font-size: 28px; margin-bottom: 8px; font-weight: 900; border: none; margin-top: 0; }}
            .date {{ color: #6b7280; font-size: 14px; margin-bottom: 24px; font-weight: 500; }}
            .subtitle {{ font-size: 15px; color: #4b5563; margin-bottom: 0; }}
            .schedule-container {{ display: flex; flex-direction: column; gap: 20px; }}
            .schedule-card {{ background: #ffffff; border: 1px solid #e4e4e7; border-radius: 16px; padding: 24px; }}
            .schedule-header {{ display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 12px; }}
            .schedule-title {{ font-size: 18px; font-weight: 900; color: #111827; }}
            .update-badge {{ background: #fee2e2; color: #dc2626; font-size: 10px; padding: 4px 8px; border-radius: 9999px; font-weight: 700; letter-spacing: 0.5px; white-space: nowrap; }}
            .schedule-time {{ color: #4b5563; font-size: 14px; font-weight: 500; margin-bottom: 20px; }}
            .section-title {{ font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 8px; }}
            .member-list {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }}
            .member-badge {{ background-color: #fafafa; color: #52525b; border: 1px solid #e4e4e7; padding: 4px 12px; border-radius: 9999px; font-size: 13px; font-weight: 500; }}
            .ticket-list {{ list-style-type: none; padding: 0; display: flex; flex-direction: column; gap: 10px; margin: 0; }}
            .ticket-list li {{ background: #fafafa; border: 1px solid #f4f4f5; border-radius: 12px; padding: 12px 16px; font-size: 13px; color: #3f3f46; font-weight: 500; }}
            .ticket-list li strong {{ color: #18181b; font-size: 14px; }}
            .footer {{ margin-top: 32px; font-size: 14px; color: #6b7280; font-weight: 500; text-align: center; }}
        </style>
        </head>
        <body>
            <div class="schedule-container">
                <div class="schedule-card">
                    <h1>Informasi Jadwal & Lineup Terbaru</h1>
                    <div class="date">{today_str}</div>
                    <p class="subtitle">Terima kasih atas dukungannya untuk JKT48.<br>Berikut adalah informasi mengenai jadwal dan lineup terbaru</p>
                </div>
                {content_html}
            </div>
        </body>
        </html>
        """

    async def _daily_reminder_loop(self, stop_event: asyncio.Event):
        last_sent_date = None

        while not stop_event.is_set():
            tz_wib = timezone(timedelta(hours=7))
            now = datetime.now(tz_wib)

            # Check if it's 12:00 PM WIB (between 12:00 and 12:01)
            if now.hour == 12 and now.minute == 0:
                today_date = now.date()
                if last_sent_date != today_date:
                    self.log.info("Running daily schedule reminder check...")
                    await self._check_daily_schedules(now)
                    last_sent_date = today_date

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=30)
            except asyncio.TimeoutError:
                pass

    async def _check_daily_schedules(self, now_wib: datetime):
        month = now_wib.month
        year = now_wib.year
        today_str = now_wib.strftime("%Y-%m-%d")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://jkt48.com/theater/schedule",
            "Origin": "https://jkt48.com",
        }

        try:
            today_schedules = []
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                url = f"https://jkt48.com/api/v1/schedules?lang=id&month={month}&year={year}"
                resp = await client.get(url)
                if not resp.is_success:
                    self.log.warning("Daily reminder failed to fetch schedules.")
                    return

                data = resp.json()
                schedules = data.get("data", [])

                # Filter for today
                for sch in schedules:
                    if sch.get("date") == today_str:
                        sch_id = str(sch.get("schedule_id"))
                        if not sch_id:
                            continue

                        members = []
                        sales_period = []
                        if sch.get("type") == "SHOW" and sch.get("reference_code"):
                            fetched_members, fetched_sales = await self._fetch_detail(
                                client, sch.get("reference_code")
                            )
                            if fetched_members is None:
                                current_state = self._get_schedule_state()
                                if sch_id in current_state:
                                    members = current_state[sch_id].get("members", [])
                                    sales_period = current_state[sch_id].get(
                                        "sales_period", []
                                    )
                            else:
                                members = fetched_members
                                sales_period = fetched_sales

                        sch_data = {
                            "title": sch.get("title", ""),
                            "date": sch.get("date", ""),
                            "start_time": sch.get("start_time", ""),
                            "type": sch.get("type", ""),
                            "jkt48_member_type": sch.get("jkt48_member_type", ""),
                            "members": members,
                            "sales_period": sales_period,
                            "id": sch_id,
                            "link": sch.get("link", ""),
                            "reference_code": sch.get("reference_code", ""),
                        }
                        today_schedules.append(sch_data)

            if today_schedules:
                self.log.info(
                    "Sending daily reminder for %d schedules.", len(today_schedules)
                )

                payload = {
                    "schedules": today_schedules,
                }

                await send_daily_schedule_reminder(payload, self.config)

        except Exception:
            self.log.exception("Exception in daily reminder:")

    async def run(self, stop_event: asyncio.Event):
        # Start the daily reminder loop in background
        reminder_task = asyncio.create_task(self._daily_reminder_loop(stop_event))

        while not stop_event.is_set():
            await self._check_schedules()

            try:
                await asyncio.wait_for(
                    stop_event.wait(), timeout=self.config.news_check_interval
                )
            except asyncio.TimeoutError:
                pass

        # Wait for reminder loop to finish
        await reminder_task
