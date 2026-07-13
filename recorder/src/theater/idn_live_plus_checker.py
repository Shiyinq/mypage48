import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone

import httpx

from ..config import RecorderConfig
from ..notify.telegram_notifier import _format_date_wib
from .html_screenshot import capture_html_screenshot

IDN_LOGO_URL = "https://www.idn.app/_next/static/media/logo_light.d99f40cc.svg"


def _clean_title(title: str) -> str:
    """Remove trailing date suffix like ' - 2026/07/16' from title.
    If the pattern doesn't match, return the original title unchanged."""
    return re.sub(r"\s*-\s*\d{4}/\d{2}/\d{2}$", "", title).strip() or title


class IdnLivePlusChecker:
    def __init__(self, config: RecorderConfig):
        self.config = config
        self.log = logging.getLogger("theater")
        self.theater_dir = self.config.theater_dir
        self.state_file = os.path.join(self.theater_dir, "idn_live_plus_state.json")
        self.pending_dir = os.path.join(self.theater_dir, "pending_notifications")

        os.makedirs(self.theater_dir, exist_ok=True)
        os.makedirs(self.pending_dir, exist_ok=True)

    def _get_state(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_state(self, state: dict):
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    async def _fetch_scheduled_lives(self) -> list[dict] | None:
        url = f"{self.config.api_base_url.rstrip('/')}/jkt48/live/scheduled"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.is_success:
                    data = resp.json()
                    return data.get("data", [])
                else:
                    self.log.warning(
                        "Failed to fetch IDN Live Plus schedules: HTTP %s",
                        resp.status_code,
                    )
                    return None
        except Exception as e:
            self.log.warning("Exception fetching IDN Live Plus schedules: %s", e)
            return None

    async def _check_scheduled_lives(self):
        self.log.info("Checking IDN Live Plus scheduled lives...")

        lives = await self._fetch_scheduled_lives()
        if lives is None:
            return

        now_utc = datetime.now(timezone.utc)
        current_state = self._get_state()
        new_state = dict(current_state)

        new_schedules = []
        updated_schedules = []

        for live in lives:
            live_id = live.get("live_id")
            if not live_id:
                continue

            title = live.get("title", "")
            scheduled_at = live.get("scheduled_at", "")
            image = live.get("image", "")

            live_data = {
                "live_id": live_id,
                "title": title,
                "scheduled_at": scheduled_at,
                "image": image,
            }

            if live_id not in current_state:
                new_schedules.append(live_data)
                new_state[live_id] = {
                    "title": title,
                    "scheduled_at": scheduled_at,
                }
            else:
                old = current_state[live_id]
                changes = []
                if old.get("title") != title:
                    changes.append("JUDUL")
                if old.get("scheduled_at") != scheduled_at:
                    changes.append("TANGGAL")

                if changes:
                    live_data["update_types"] = changes
                    updated_schedules.append(live_data)

                new_state[live_id] = {
                    "title": title,
                    "scheduled_at": scheduled_at,
                }

        # Cleanup old entries that have already passed
        for lid in list(new_state.keys()):
            sa = new_state[lid].get("scheduled_at", "")
            if sa:
                try:
                    dt = datetime.fromisoformat(sa.replace("Z", "+00:00"))
                    if dt < now_utc:
                        del new_state[lid]
                except Exception:
                    pass

        if new_schedules or updated_schedules:
            self.log.info(
                "IDN Live Plus: %d new, %d updated schedules.",
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

                await self._generate_and_send_notification(chunk_new, chunk_updated)
                await asyncio.sleep(1.5)

            self._save_state(new_state)
        else:
            self.log.debug("No new IDN Live Plus schedules or updates found.")

    async def _generate_and_send_notification(self, new_schedules, updated_schedules):
        timestamp_ms = int(time.time() * 1000)
        screenshot_path = os.path.join(
            self.pending_dir, f"idn_live_plus_{timestamp_ms}.jpg"
        )

        html_content = self._generate_html(new_schedules, updated_schedules)

        success = await capture_html_screenshot(
            html_content, screenshot_path, wait_ms=1000
        )

        payload = {
            "type": "idn_live_plus",
            "new_count": len(new_schedules),
            "updated_count": len(updated_schedules),
            "screenshot_path": screenshot_path if success else None,
            "timestamp": timestamp_ms,
            "new_schedules": new_schedules,
            "updated_schedules": updated_schedules,
        }

        payload_file = os.path.join(
            self.pending_dir, f"idn_live_plus_{timestamp_ms}.json"
        )
        with open(payload_file, "w") as f:
            json.dump(payload, f, indent=2)

        self.log.info("Prepared IDN Live Plus notification payload: %s", payload_file)

    def _generate_html(self, new_schedules, updated_schedules) -> str:
        tz_wib = timezone(timedelta(hours=7))
        today_wib = datetime.now(tz_wib)

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

        day_name = ID_DAYS[today_wib.weekday()]
        today_str = (
            f"{day_name}, {today_wib.day} {ID_MONTHS[today_wib.month]} {today_wib.year}"
        )

        def render_schedule(sch, is_update=False):
            title = _clean_title(sch.get("title", ""))
            scheduled_at = sch.get("scheduled_at", "")
            image = sch.get("image", "")

            date_wib = _format_date_wib(scheduled_at) if scheduled_at else ""

            if is_update:
                types = sch.get("update_types", [])
                types_str = " & ".join(types)
                badge_html = f"<span class='update-badge'>UPDATE {types_str}</span>"
            else:
                badge_html = "<span class='update-badge'>BARU</span>"

            image_html = ""
            if image:
                image_html = f'<img class="schedule-image" src="{image}" alt="{title}">'

            return f"""
                <div class="schedule-card">
                    <div class="schedule-body">
                        {image_html}
                        <div class="schedule-info">
                            <div class="schedule-header">
                                <span class="schedule-title">{title}</span>
                                {badge_html}
                            </div>
                            <div class="schedule-time">📅 {date_wib}</div>
                        </div>
                    </div>
                </div>
            """

        content_html = ""
        for sch in new_schedules:
            content_html += render_schedule(sch, is_update=False)
        for sch in updated_schedules:
            content_html += render_schedule(sch, is_update=True)

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
            .header-logo {{ height: 32px; margin-bottom: 16px; }}
            .date {{ color: #6b7280; font-size: 14px; margin-bottom: 24px; font-weight: 500; }}
            .subtitle {{ font-size: 15px; color: #4b5563; margin-bottom: 0; }}
            .schedule-container {{ display: flex; flex-direction: column; gap: 20px; }}
            .schedule-card {{ background: #ffffff; border: 1px solid #e4e4e7; border-radius: 16px; padding: 20px; }}
            .schedule-body {{ display: flex; align-items: center; gap: 16px; }}
            .schedule-image {{ width: 120px; height: 120px; object-fit: cover; border-radius: 12px; flex-shrink: 0; }}
            .schedule-info {{ flex: 1; min-width: 0; }}
            .schedule-header {{ display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 8px; }}
            .schedule-title {{ font-size: 16px; font-weight: 900; color: #111827; }}
            .update-badge {{ background: #fee2e2; color: #dc2626; font-size: 10px; padding: 4px 8px; border-radius: 9999px; font-weight: 700; letter-spacing: 0.5px; white-space: nowrap; }}
            .schedule-time {{ color: #4b5563; font-size: 13px; font-weight: 500; }}
            .footer {{ margin-top: 32px; font-size: 14px; color: #6b7280; font-weight: 500; text-align: center; }}
        </style>
        </head>
        <body>
            <div class="schedule-container">
                <div class="schedule-card">
                    <img class="header-logo" src="{IDN_LOGO_URL}" alt="IDN Live">
                    <h1>Jadwal IDN Live Plus</h1>
                    <div class="date">{today_str}</div>
                    <p class="subtitle">Berikut adalah informasi mengenai jadwal terbaru di IDN Live Plus</p>
                </div>
                {content_html}
            </div>
        </body>
        </html>
        """

    async def run(self, stop_event: asyncio.Event):
        while not stop_event.is_set():
            await self._check_scheduled_lives()

            try:
                await asyncio.wait_for(
                    stop_event.wait(), timeout=self.config.schedule_check_interval
                )
            except asyncio.TimeoutError:
                pass
