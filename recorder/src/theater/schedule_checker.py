import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone

import httpx

from ..config import RecorderConfig
from ..notify.telegram_notifier import _format_date_only_wib
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
    ) -> tuple[list[str], list[dict]]:
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
        except Exception as e:
            self.log.warning("Exception fetching schedule detail %s: %s", ref_code, e)
        return [], []

    async def _check_schedules(self):
        self.log.info("Checking JKT48 schedules...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://jkt48.com/theater/schedule",
            "Origin": "https://jkt48.com",
        }

        # MOCK DATE to July 1st, 2026
        today_wib = datetime(2026, 7, 1, 10, 0, tzinfo=timezone(timedelta(hours=7)))

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
                            members, sales_period = await self._fetch_detail(
                                client, sch.get("reference_code")
                            )

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

    def _generate_html(self, new_schedules, updated_schedules) -> str:
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

        def render_schedule(sch, is_update=False):
            if is_update:
                types = sch.get("update_types", ["MEMBER"])
                badge_text = f"[UPDATE {' & '.join(types)}]"
            else:
                badge_text = "[BARU]"

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
                members_html = f"<br><br><strong>Anggota yang tampil:</strong><div class='member-list'>{members_badges}</div>"
            else:
                if sch["type"] == "SHOW":
                    members_html = '<br><br><strong>Anggota yang tampil:</strong><div class="member-list"><em>Belum tersedia</em></div>'

            sales_html = ""
            if sch.get("sales_period"):
                sales_html += "<strong>Info Tiket:</strong><ul class='ticket-list'>"
                for sp in sch["sales_period"]:
                    lbl = sp.get("label", "")
                    start_d = format_ticket_date(sp.get("start_date", ""))
                    end_d = format_ticket_date(sp.get("end_date", ""))

                    quotas = []
                    for pricing in sp.get("pricing", []):
                        if "quota" in pricing:
                            quotas.append(f"{pricing.get('quota')} tiket")
                    quota_str = ""
                    if quotas:
                        quota_str = f" (Quota: {', '.join(quotas)})"

                    sales_html += f"<li>{lbl}: {start_d} - {end_d}{quota_str}</li>"
                sales_html += "</ul>"

            return f"""
                <li class="schedule-item">
                    <strong>{badge_text} {title_text}</strong><br>
                    {date_wib} • {time_str} WIB{members_html}{sales_html}
                </li>
            """

        # MOCK DATE to July 1st, 2026
        today_wib = datetime(2026, 7, 1, 10, 0, tzinfo=timezone(timedelta(hours=7)))
        today_str = _format_date_only_wib(today_wib.isoformat())

        content_html = "<p>Terima kasih atas dukungannya untuk JKT48.</p><p>Berikut adalah informasi mengenai jadwal dan lineup terbaru:</p><ul>"

        if new_schedules:
            for sch in new_schedules:
                content_html += render_schedule(sch, is_update=False)

        if updated_schedules:
            for sch in updated_schedules:
                content_html += render_schedule(sch, is_update=True)

        content_html += "</ul><br><p>Mohon dukungannya selalu untuk JKT48.</p>"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 40px; background: #fff; color: #333; line-height: 1.6; max-width: 800px; margin: 0 auto; }}
            h1 {{ color: #d6001c; font-size: 26px; margin-bottom: 10px; border-bottom: 2px solid #eee; padding-bottom: 15px; }}
            .date {{ color: #777; font-size: 14px; margin-bottom: 30px; font-weight: bold; }}
            .content {{ font-size: 16px; }}
            ul {{ margin-bottom: 20px; }}
            .schedule-item {{ margin-bottom: 25px; }}
            .member-list {{ margin-top: 10px; margin-bottom: 25px; }}
            .ticket-list {{ margin-top: 5px; list-style-type: circle; margin-bottom: 0; }}
            .ticket-list li {{ margin-bottom: 5px; font-size: 14px; }}
            .member-badge {{
                background-color: #fee2e2;
                color: #dc2626;
                padding: 4px 12px;
                border-radius: 9999px;
                display: inline-block;
                margin-right: 6px;
                margin-bottom: 8px;
                font-size: 14px;
            }}
        </style>
        </head>
        <body>
            <h1>Informasi Jadwal & Lineup Terbaru</h1>
            <div class="date">{today_str}</div>
            <div class="content">{content_html}</div>
        </body>
        </html>
        """

    async def run(self, stop_event: asyncio.Event):
        while not stop_event.is_set():
            await self._check_schedules()

            try:
                await asyncio.wait_for(
                    stop_event.wait(), timeout=self.config.news_check_interval
                )
                break
            except asyncio.TimeoutError:
                pass
