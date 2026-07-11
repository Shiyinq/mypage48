import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from ..config import RecorderConfig
from ..notify.telegram_notifier import send_birthday_notification


class BirthdayChecker:
    def __init__(self, config: RecorderConfig):
        self.config = config
        self.log = logging.getLogger("theater")

    async def _check_birthdays(self, now_wib: datetime):
        self.log.info("Checking member birthdays for %s", now_wib.strftime("%Y-%m-%d"))
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

                birthday_members = [m for m in data if m.get("days_until") == 0]

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
