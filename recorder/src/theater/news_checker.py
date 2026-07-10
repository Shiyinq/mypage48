import asyncio
import base64
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone

import httpx

from ..config import RecorderConfig
from ..notify.telegram_notifier import _format_date_only_wib
from .html_screenshot import capture_html_screenshot


class NewsChecker:
    def __init__(self, config: RecorderConfig):
        self.config = config
        self.log = logging.getLogger("theater")
        self.api_url = "https://jkt48.com/api/v1/news?lang=id&page=1"
        self.theater_dir = self.config.theater_dir
        self.state_file = os.path.join(self.theater_dir, "last_news_id.json")
        self.pending_dir = os.path.join(self.theater_dir, "pending_notifications")

        os.makedirs(self.theater_dir, exist_ok=True)
        os.makedirs(self.pending_dir, exist_ok=True)

    def _get_processed_ids(self) -> list:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    if "last_news_id" in data:
                        return [data["last_news_id"]]
                    return data.get("processed_ids", [])
            except Exception:
                return []
        return []

    def _save_processed_ids(self, processed_ids: list):
        # Keep only the last 200 IDs
        processed_ids = processed_ids[-200:]
        with open(self.state_file, "w") as f:
            json.dump({"processed_ids": processed_ids}, f)

    async def _embed_images_in_html(
        self, html_content: str, client: httpx.AsyncClient, current_news_id: int
    ) -> tuple[str, list]:
        """Download images, save them locally for telegram, and embed them as base64."""
        img_urls = re.findall(
            r'<img[^>]+src=["\'](.*?)["\']', html_content, re.IGNORECASE
        )
        saved_images = []
        img_count = 0

        for url in img_urls:
            if not url or url.startswith("data:"):
                continue

            full_url = url
            if full_url.startswith("/"):
                full_url = "https://jkt48.com" + full_url

            if not full_url.startswith("http"):
                continue

            try:
                # Add headers to mimic browser request
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://jkt48.com/",
                }
                resp = await client.get(full_url, headers=headers, timeout=15.0)
                if resp.is_success:
                    content_type = resp.headers.get("content-type", "image/jpeg")
                    # Some JKT48 images return application/octet-stream, so we force image/jpeg
                    if "octet-stream" in content_type:
                        content_type = "image/jpeg"

                    b64_data = base64.b64encode(resp.content).decode("utf-8")
                    data_uri = f"data:{content_type};base64,{b64_data}"
                    html_content = html_content.replace(url, data_uri)

                    # Save locally for Telegram MediaGroup
                    img_count += 1
                    ext = "jpg" if "jpeg" in content_type else "png"
                    local_path = os.path.join(
                        self.pending_dir,
                        f"news_{current_news_id}_img_{img_count}.{ext}",
                    )
                    with open(local_path, "wb") as f:
                        f.write(resp.content)
                    saved_images.append(local_path)
                else:
                    self.log.warning(
                        "Failed to download image %s: HTTP %s",
                        full_url,
                        resp.status_code,
                    )
            except Exception as e:
                self.log.warning("Exception downloading image %s: %s", full_url, e)

        return html_content, saved_images

    async def _check_news(self):
        self.log.info("Checking JKT48 news...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://jkt48.com/news",
            "Origin": "https://jkt48.com",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                resp = await client.get(self.api_url)
                if not resp.is_success:
                    self.log.warning("Failed to fetch news: %s", resp.status_code)
                    return

                data = resp.json()
                news_list = data.get("data", [])
                if not news_list:
                    return

                processed_ids = self._get_processed_ids()
                new_processed_ids = list(processed_ids)
                today_wib = datetime.now(timezone(timedelta(hours=7))).date()
                # today_wib = datetime(2026, 6, 13).date()

                new_news_found = False

                for news_item in news_list:
                    current_news_id = news_item.get("news_id", 0)
                    if not current_news_id or current_news_id in processed_ids:
                        continue

                    valid_date_str = news_item.get("valid_date_from")
                    if not valid_date_str:
                        continue

                    try:
                        dt = datetime.fromisoformat(
                            valid_date_str.replace("Z", "+00:00")
                        )
                        news_date_wib = dt.astimezone(
                            timezone(timedelta(hours=7))
                        ).date()
                    except Exception:
                        continue

                    if news_date_wib >= today_wib:
                        new_news_found = True
                        self.log.info(
                            "New news detected: %s (ID: %s)",
                            news_item.get("title"),
                            current_news_id,
                        )

                        link = news_item.get("link")
                        if not link:
                            self.log.warning("News has no link, skipping screenshot.")
                            continue

                        news_url = f"https://jkt48.com/news/{link}"
                        detail_api_url = f"https://jkt48.com/api/v1/news/{link}?lang=id&preview=false"
                        screenshot_name = f"news_{current_news_id}.jpg"
                        screenshot_path = os.path.join(
                            self.pending_dir, screenshot_name
                        )

                        # Fetch detail API
                        detail_resp = await client.get(detail_api_url)
                        success = False
                        if detail_resp.is_success:
                            detail_data = detail_resp.json()
                            content_body = (
                                detail_data.get("data", {})
                                .get("result", {})
                                .get("content_body", "")
                            )

                            # Download and embed images directly into the HTML, and get paths
                            (
                                content_body,
                                article_images,
                            ) = await self._embed_images_in_html(
                                content_body, client, current_news_id
                            )

                            date_str = _format_date_only_wib(
                                news_item.get("valid_date_from", "")
                            )
                            title_str = news_item.get("title", "")

                            html_content = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                            <meta charset="utf-8">
                            <base href="https://jkt48.com/">
                            <style>
                                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 40px; background: #fff; color: #333; line-height: 1.6; max-width: 800px; margin: 0 auto; }}
                                h1 {{ color: #d6001c; font-size: 26px; margin-bottom: 10px; border-bottom: 2px solid #eee; padding-bottom: 15px; }}
                                .date {{ color: #777; font-size: 14px; margin-bottom: 30px; font-weight: bold; }}
                                .content {{ font-size: 16px; }}
                                .content img {{ max-width: 100%; height: auto; }}
                                .content a {{ color: #d6001c; text-decoration: none; }}
                            </style>
                            </head>
                            <body>
                                <h1>{title_str}</h1>
                                <div class="date">{date_str}</div>
                                <div class="content">{content_body}</div>
                            </body>
                            </html>
                            """
                            # Capture HTML screenshot
                            success = await capture_html_screenshot(
                                html_content, screenshot_path, wait_ms=1000
                            )
                        else:
                            self.log.warning(
                                "Failed to fetch detail news API: %s",
                                detail_resp.status_code,
                            )

                        payload = {
                            "type": "news",
                            "news_id": current_news_id,
                            "title": news_item.get("title"),
                            "category": news_item.get("category"),
                            "valid_date_from": news_item.get("valid_date_from"),
                            "link": link,
                            "url": news_url,
                            "screenshot_path": screenshot_path if success else None,
                            "article_images": article_images if success else [],
                            "timestamp": time.time(),
                        }

                        # Save payload
                        payload_file = os.path.join(
                            self.pending_dir, f"news_{current_news_id}.json"
                        )
                        with open(payload_file, "w") as f:
                            json.dump(payload, f, indent=2)

                        # Update state immediately in case of crash during loop
                        new_processed_ids.append(current_news_id)
                        self._save_processed_ids(new_processed_ids)
                        self.log.info(
                            "Successfully prepared news notification payload: %s",
                            payload_file,
                        )

                if not new_news_found:
                    self.log.debug(
                        "No new news found today. Processed IDs count: %d",
                        len(processed_ids),
                    )

        except Exception:
            self.log.exception("Exception during news check:")

    async def run(self, stop_event: asyncio.Event):
        while not stop_event.is_set():
            await self._check_news()

            # Sleep for configured interval (default 15 minutes)
            try:
                await asyncio.wait_for(
                    stop_event.wait(), timeout=self.config.news_check_interval
                )
                break
            except asyncio.TimeoutError:
                pass
