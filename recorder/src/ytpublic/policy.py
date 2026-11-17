"""Pure, fail-closed publication policy for YouTube video resources."""

import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from numbers import Real
from typing import Iterable


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    rule: str | None = None
    start_at: datetime | None = None
    eligible_at: datetime | None = None


_WIB = timezone(timedelta(hours=7))
_MONTHS = {
    name: index
    for index, name in enumerate(
        "januari februari maret april mei juni juli agustus september oktober "
        "november desember".split(),
        start=1,
    )
}
_WEEKDAYS = "senin selasa rabu kamis jumat sabtu minggu".split()
_IDN_TITLE = re.compile(
    r"live idn (?P<member>[^|]+) jkt48 \| "
    r"(?P<weekday>[a-z]+), (?P<day>[0-9]{1,2}) (?P<month>[a-z]+) "
    r"(?P<year>[0-9]{4}) (?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}) wib"
)


def evaluate_video(
    video: dict,
    now: datetime,
    *,
    base_delay_hours=72,
    buffer_hours=8,
    excluded_ids: Iterable[str] = (),
    already_published=False,
) -> Decision:
    """Evaluate a YouTube ``snippet``/``status`` resource without side effects.

    IDN timestamps are returned in UTC. SHOWROOM decisions have no timestamps.
    Invalid configuration and naive comparison times are caller errors.
    """
    for value, minimum, name in (
        (base_delay_hours, 72, "base_delay_hours"),
        (buffer_hours, 0, "buffer_hours"),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, Real)
            or not math.isfinite(value)
            or value < minimum
        ):
            raise ValueError(f"{name} must be finite and >= {minimum}")
    try:
        delay = timedelta(hours=base_delay_hours) + timedelta(hours=buffer_hours)
    except OverflowError as exc:
        raise ValueError("publication delay is too large") from exc
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ValueError("now must be a timezone-aware datetime")

    if already_published:
        return Decision("skip", "already_published")
    if video.get("id") in excluded_ids:
        return Decision("skip", "excluded_id")
    status = video.get("status")
    if not isinstance(status, dict):
        status = {}
    privacy = status.get("privacyStatus")
    if privacy != "private":
        reason = {"public": "public", "unlisted": "unlisted"}.get(
            privacy if isinstance(privacy, str) else None, "unknown_status"
        )
        return Decision("skip", reason)
    if status.get("publishAt"):
        return Decision("skip", "scheduled")

    snippet = video.get("snippet")
    title = snippet.get("title") if isinstance(snippet, dict) else None
    if not isinstance(title, str):
        return Decision("skip", "invalid_title")
    title = " ".join(title.split()).casefold()
    if not title:
        return Decision("skip", "invalid_title")
    if re.match(r"live idn jkt48\b", title):
        return Decision("skip", "official_idn", "idn")
    has_idn = bool(re.search(r"\bidn\b", title))
    has_showroom = bool(re.search(r"\bshowroom\b", title))
    if has_idn and has_showroom:
        return Decision("skip", "mixed_platforms")
    if has_showroom:
        return Decision("eligible", "showroom_immediate", "showroom")

    match = _IDN_TITLE.fullmatch(title)
    if match is None:
        return Decision("skip", "invalid_idn_title" if has_idn else "unsupported_title")
    parts = match.groupdict()
    month = _MONTHS.get(parts["month"])
    year = int(parts["year"])
    if month is None or not 2000 <= year <= 2100:
        return Decision("skip", "invalid_idn_date", "idn")
    try:
        start = datetime(
            year,
            month,
            int(parts["day"]),
            int(parts["hour"]),
            int(parts["minute"]),
            tzinfo=_WIB,
        )
    except ValueError:
        return Decision("skip", "invalid_idn_date", "idn")
    if parts["weekday"] != _WEEKDAYS[start.weekday()]:
        return Decision("skip", "weekday_mismatch", "idn")
    start = start.astimezone(timezone.utc)
    try:
        eligible = start + delay
    except OverflowError as exc:
        raise ValueError("publication delay is too large") from exc
    if now < eligible:
        return Decision("wait", "idn_delay", "idn", start, eligible)
    return Decision("eligible", "idn_ready", "idn", start, eligible)
