import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from ..config import RecorderConfig
from ..notify.telegram_notifier import (
    send_birthday_notification,
    send_monthly_birthday_list,
)

MONTHS_ID = [
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


class BirthdayChecker:
    def __init__(self, config: RecorderConfig):
        self.config = config
        self.log = logging.getLogger("theater")

    async def _check_birthdays(self, now_wib: datetime):
        self.log.info("Checking member birthdays for %s", now_wib.strftime("%Y-%m-%d"))

        if now_wib.day == 1:
            await self._send_monthly_birthday_list(now_wib)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                api_url = f"{self.config.api_base_url}/members/birthdays"
                resp = await client.get(api_url)
                if not resp.is_success:
                    self.log.warning(
                        "Failed to fetch birthdays: HTTP %s", resp.status_code
                    )
                    return

                data = resp.json()

                current_month_name = MONTHS_ID[now_wib.month - 1]
                current_day_str = str(now_wib.day).zfill(2)

                birthday_members = []
                for m in data:
                    b_date = m.get("birthdate", "")
                    if not b_date:
                        continue

                    parts = b_date.split(" ")
                    if len(parts) >= 2:
                        m_day = parts[0].zfill(2)
                        m_month = parts[1]

                        if (
                            m_day == current_day_str
                            and m_month.lower() == current_month_name.lower()
                        ):
                            if len(parts) >= 3:
                                try:
                                    birth_year = int(parts[2])
                                    m["age"] = now_wib.year - birth_year
                                except:
                                    pass
                            birthday_members.append(m)

                if not birthday_members:
                    self.log.info("No members have a birthday today.")
                    return

                self.log.info(
                    "Found %d members with birthday today.", len(birthday_members)
                )

                for member in birthday_members:
                    await send_birthday_notification(member, self.config)

        except Exception:
            self.log.exception("Exception in birthday checker:")

    async def _send_monthly_birthday_list(self, now_wib: datetime):
        month_name = MONTHS_ID[now_wib.month - 1]

        self.log.info("Fetching monthly birthday list for %s", month_name)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                api_url = f"{self.config.api_base_url}/members?limit=100"
                resp = await client.get(api_url)
                if not resp.is_success:
                    self.log.warning(
                        "Failed to fetch members for monthly birthday list: HTTP %s",
                        resp.status_code,
                    )
                    return

                data = resp.json()
                members_data = data.get("data", [])

                month_members = []
                for m in members_data:
                    b_date = m.get("birthdate", "")
                    if not b_date:
                        continue

                    parts = b_date.split(" ")
                    if len(parts) >= 3:
                        m_month = parts[1]
                        if m_month.lower() == month_name.lower():
                            # Calculate age
                            try:
                                birth_year = int(parts[2])
                                m["new_age"] = now_wib.year - birth_year
                            except:
                                m["new_age"] = "?"
                            month_members.append(m)

                if not month_members:
                    self.log.info("No birthdays found for %s", month_name)
                    return

                # Sort by date (day)
                def get_day(member):
                    try:
                        return int(member.get("birthdate", "").split(" ")[0])
                    except:
                        return 99

                month_members.sort(key=get_day)

                await send_monthly_birthday_list(month_name, month_members, self.config)

        except Exception:
            self.log.exception("Exception in monthly birthday list sender:")

    async def _daily_birthday_loop(self, stop_event: asyncio.Event):
        last_sent_date = None

        while not stop_event.is_set():
            tz_wib = timezone(timedelta(hours=7))
            now = datetime.now(tz_wib)

            # Check if it's 00:00 AM WIB (between 00:00 and 00:01)
            if now.hour == 0 and now.minute == 0:
                today_date = now.date()
                if last_sent_date != today_date:
                    self.log.info("Running daily birthday check...")
                    await self._check_birthdays(now)
                    last_sent_date = today_date

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=30)
            except asyncio.TimeoutError:
                pass

    async def run(self, stop_event: asyncio.Event):
        self.log.info("Starting Birthday Checker (trigger at 00:00 WIB)")
        await self._daily_birthday_loop(stop_event)
