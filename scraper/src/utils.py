import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple


def get_theater_id(url: str) -> Optional[str]:
    """Extract theater ID from URL."""
    match = re.search(r"/(\d+)\?", url)
    return match.group(1) if match else None


def extract_date_time(input_str: str) -> Optional[str]:
    """Extract date and time from string."""
    date_regex = r"(\d{1,2}[.:]\d{1,2}[.:]\d{4})Show (\d{1,2}[.:]\d{2})"
    match = re.search(date_regex, input_str)

    if match:
        date_str, time_str = match.groups()
        day, month, year = map(int, re.split(r"[.:]", date_str))
        hours, minutes = map(int, re.split(r"[.:]", time_str))
        from datetime import datetime

        return datetime(year, month - 1, day, hours, minutes)
    return None


def extract_id_from_url(url: str) -> str:
    """Extract member ID from URL."""
    regex = r"/member/detail/id/(\d+)"
    match = re.search(regex, url)
    return match.group(1) if match else "0"


def extract_team_id(filename: str) -> Optional[str]:
    """Extract team ID from filename."""
    parts = filename.split(".")
    return parts[1] if len(parts) >= 2 else None


def extract_date_calendar(input_str: str) -> Optional[int]:
    """Extract date number from calendar string."""
    match = re.match(r"^\d+", input_str)
    if match:
        try:
            return int(match.group(0))
        except ValueError:
            return None
    return None


def extract_year_and_month_from_url(url: str) -> Tuple[Optional[int], Optional[int]]:
    """Extract year and month from calendar URL."""
    regex = r"/y/(\d{4})/m/(\d{1,2})/"
    match = re.search(regex, url)

    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        return year, month
    return None, None


def extract_news_id(url: str) -> Optional[str]:
    """Extract news ID from URL."""
    regex = r"/id/(\d+)"
    match = re.search(regex, url)
    return match.group(1) if match else None


def slugify(text: str) -> str:
    """Simple slugify: lower, strip, and replace spaces with dashes."""
    return text.lower().strip().replace(" ", "-")


def format_birthdate_id(date_str: str) -> str:
    """Format ISO date to Indonesian (e.g., 2008-08-05 -> 06 Agustus 2008)."""
    try:
        # date_str is like "2008-08-05T17:00:00.000Z"
        dt_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        # Convert to WIB (UTC+7)
        dt_jakarta = dt_utc.astimezone(timezone(timedelta(hours=7)))
        months = [
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
        return f"{dt_jakarta.day:02d} {months[dt_jakarta.month - 1]} {dt_jakarta.year}"
    except Exception:
        return ""


def clean_jkt48_url(url: str) -> str:
    """Remove domain and storage prefix from JKT48 URLs."""
    if not url:
        return ""
    prefix = "https://jkt48.com/api/v1/storages"
    if url.startswith(prefix):
        result = url[len(prefix) :]
    else:
        result = url.replace("https://jkt48.com", "")

    if result and not result.startswith("/"):
        result = "/" + result
    return result
