import asyncio
import json
import logging
import os
from pathlib import Path

from ..config import RecorderConfig
from ..notify.telegram_notifier import send_news_notification


class TheaterWatcher:
    """Watches the pending_notifications folder and sends them to Telegram."""

    def __init__(self, config: RecorderConfig):
        self.config = config
        self.log = logging.getLogger("theater")
        self.pending_dir = os.path.join(
            self.config.theater_dir, "pending_notifications"
        )
        os.makedirs(self.pending_dir, exist_ok=True)

    async def run(self, stop_event: asyncio.Event):
        self.log.info("Starting TheaterWatcher to monitor pending notifications...")
        while not stop_event.is_set():
            await self._process_pending_notifications()

            try:
                # Poll every 10 seconds for new notifications
                await asyncio.wait_for(stop_event.wait(), timeout=10.0)
                break
            except asyncio.TimeoutError:
                pass

    async def _process_pending_notifications(self):
        if not os.path.isdir(self.pending_dir):
            return

        for filename in sorted(os.listdir(self.pending_dir)):
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(self.pending_dir, filename)

            try:
                with open(filepath, "r") as f:
                    payload = json.load(f)
            except Exception as e:
                self.log.error("Failed to read payload %s: %s", filepath, e)
                continue

            notification_type = payload.get("type")
            success = False

            if notification_type == "news":
                self.log.info("Processing pending news notification: %s", filename)
                success = await send_news_notification(payload, self.config)
            else:
                self.log.warning(
                    "Unknown notification type in %s: %s", filename, notification_type
                )
                # Treat as success to delete the unknown type and avoid infinite loop
                success = True

            if success:
                # Cleanup the JSON payload
                try:
                    os.remove(filepath)
                except Exception as e:
                    self.log.error(
                        "Failed to delete processed payload %s: %s", filepath, e
                    )

                # Cleanup associated screenshot if any
                screenshot_path = payload.get("screenshot_path")
                if screenshot_path and os.path.exists(screenshot_path):
                    try:
                        os.remove(screenshot_path)
                    except Exception as e:
                        self.log.error(
                            "Failed to delete associated screenshot %s: %s",
                            screenshot_path,
                            e,
                        )

                # Cleanup associated article images if any
                article_images = payload.get("article_images", [])
                for img_path in article_images:
                    if os.path.exists(img_path):
                        try:
                            os.remove(img_path)
                        except Exception as e:
                            self.log.error(
                                "Failed to delete associated image %s: %s", img_path, e
                            )
            else:
                self.log.warning(
                    "Failed to send notification for %s, will retry later.", filename
                )
