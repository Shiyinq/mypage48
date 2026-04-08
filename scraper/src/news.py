"""News scraper for JKT48 website."""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .agent.browser import request
from .utils import clean_jkt48_url


async def sleep(ms: int):
    """Sleep for specified milliseconds."""
    await asyncio.sleep(ms / 1000)


def parse_date_wib(date_str: str) -> Optional[datetime]:
    """Parse UTC date string to WIB datetime."""
    if not date_str:
        return None
    try:
        utc_date_str = date_str.replace("Z", "+00:00")
        if not "+" in utc_date_str and not "-" in utc_date_str[-6:]:
            utc_date_str += "+00:00"
        utc_date = datetime.fromisoformat(utc_date_str)
        wib_date = utc_date + timedelta(hours=7)
        return wib_date.replace(tzinfo=None)
    except Exception:
        return None


def get_news_page(
    page: int = 1,
    news: Optional[List[Dict[str, Any]]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Get news from a single page via API."""
    if news is None:
        news = []

    url = f"https://jkt48.com/api/v1/news?lang=id&page={page}"
    response = request("GET", url, headers=headers or {}, impersonate="chrome")
    response.raise_for_status()
    data = response.json()

    if not data.get("status") or "data" not in data:
        return sorted(news, key=lambda x: x.get("link", ""))

    for item in data["data"]:
        item.get("link", "")

        # Clean background image URL
        bg_image = item.get("background_image", "")
        if bg_image:
            item["background_image"] = clean_jkt48_url(bg_image)

        news.append(
            {
                **item,  # Include all raw fields from the API
                "title": item.get("title") or "",
            }
        )

    return news


def get_all_news(
    page: int = 1,
    news: Optional[List[Dict[str, Any]]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Get all news with pagination."""
    if news is None:
        news = []

    url = f"https://jkt48.com/api/v1/news?lang=id&page={page}"
    response = request("GET", url, headers=headers or {}, impersonate="chrome")
    response.raise_for_status()
    data = response.json()

    if not data.get("status") or "data" not in data or not data["data"]:
        return news

    for item in data["data"]:
        # Clean background image URL
        bg_image = item.get("background_image", "")
        if bg_image:
            item["background_image"] = clean_jkt48_url(bg_image)

        news.append(
            {
                **item,
                "title": item.get("title") or "",
            }
        )

    # Check for next page
    meta = data.get("_meta", {})
    current_page = meta.get("page", page)
    last_page = meta.get("total_page", page)

    print(f"  - Listing: Page {current_page}/{last_page}", end="\r", flush=True)

    if current_page < last_page:
        time.sleep(0.5)
        return get_all_news(page + 1, news, headers)

    print()  # Finish listing
    return news


def get_news(news_id: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Get single news detail via API."""
    url = f"https://jkt48.com/api/v1/news/{news_id}?lang=id&preview=false"

    response = request("GET", url, headers=headers or {}, impersonate="chrome")
    response.raise_for_status()
    data = response.json()

    if not data.get("status") or "data" not in data:
        return {}

    raw_detail = data["data"].get("result", {})

    # Clean background image URL
    bg_image = raw_detail.get("background_image", "")
    if bg_image:
        raw_detail["background_image"] = clean_jkt48_url(bg_image)

    return {
        **raw_detail,
        "title": raw_detail.get("title") or "",
    }
