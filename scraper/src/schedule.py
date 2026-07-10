import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .agent.browser import request
from .utils import slugify


def _get_id_mapping() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Get mapping from current JKT48 ID to legacy app ID and Name to legacy app ID."""
    id_map = {}
    name_map = {}

    # Use absolute path relative to this file
    legacy_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "active.members.json"
    )

    if os.path.exists(legacy_file):
        try:
            with open(legacy_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for m in data:
                    # Priority for mapping: jkt48_id (Official) -> id (Legacy)
                    # If jkt48_id is missing, assume the current 'id' is the one from API (for legacy support)
                    official_id = m.get("jkt48_id") or m.get("id")
                    legacy_id = m.get("id")
                    name = m.get("name", "").strip().lower()

                    if official_id and legacy_id:
                        id_map[str(official_id)] = str(legacy_id)
                    if name and legacy_id:
                        name_map[name] = str(legacy_id)
        except Exception as e:
            print(f"Warning: Could not load ID mapping: {e}")
    return id_map, name_map


def _get_event_url(event_type: str, code: str, slug: str, title: str = "") -> str:
    """Generate correct JKT48 URL based on event type."""
    if event_type == "SHOW":
        return f"/purchase/schedule/show?code={code}"
    elif event_type == "EXCLUSIVE":
        return f"/purchase/exclusive?code={code}"
    elif event_type == "EVENT":
        return f"/purchase/schedule/event?code={code}"
    else:
        # Default to /schedule/slug for GENERAL, etc.
        url_slug = slug or slugify(title)
        return f"/schedule/{url_slug}"


def get_schedules_by_month(
    year: int, month: int, headers: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """Get all calendar events from API for a specific month and year."""
    url = f"https://jkt48.com/api/v1/schedules?lang=id&month={month}&year={year}"
    response = request("GET", url, headers=headers or {}, impersonate="chrome")
    response.raise_for_status()
    data = response.json()

    if not data.get("status") or "data" not in data:
        return []

    schedules = data["data"]
    events = []

    for item in schedules:
        # Date handling: UTC to WIB (+7)
        try:
            utc_date_str = item.get("date", "").replace("Z", "+00:00")
            if not "+" in utc_date_str and not "-" in utc_date_str[-6:]:
                utc_date_str += "+00:00"

            utc_date = datetime.fromisoformat(utc_date_str)
            wib_date = utc_date + timedelta(hours=7)

            start_time_str = item.get("start_time")
            if start_time_str:
                parts = start_time_str.split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                wib_date = wib_date.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

            wib_date = wib_date.replace(tzinfo=None)
        except Exception:
            wib_date = datetime.now()

        event_type = item.get("type", "EVENT")
        schedule_id = str(item.get("schedule_id", ""))

        # EXCLUSIVE events often share the same reference_code for multiple dates.
        # For these, we MUST use schedule_id to avoid data collision in the DB.
        if event_type == "EXCLUSIVE":
            id_val = schedule_id
        else:
            # For SHOW and other types, we prioritize reference_code for consistency
            id_val = str(item.get("reference_code") or schedule_id)

        # For URL generation, we ALWAYS want the reference_code if it exists.
        url_code = str(item.get("reference_code") or schedule_id)
        url_path = _get_event_url(
            event_type, url_code, item.get("link", ""), item.get("title", "")
        )
        label = item.get("jkt48_member_type") or item.get("type") or ""

        events.append(
            {
                "id": id_val,
                "label": label,
                "title": item.get("title") or "",
                "url": url_path,
                "date": wib_date,
                "type": event_type,
                "raw_data": {"short": item},
            }
        )

    return events


_members_cache: List[Dict[str, Any]] = []


def _ensure_members_cache(
    headers: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    global _members_cache
    if not _members_cache:
        try:
            url = f"https://jkt48.com/api/v1/members?lang=id"
            response = request("GET", url, headers=headers or {}, impersonate="chrome")
            response.raise_for_status()
            data = response.json()
            if data.get("status") and "data" in data:
                _members_cache = data["data"]
        except Exception:
            pass
    return _members_cache


def _find_member_id_by_name(
    name: str, headers: Optional[Dict[str, str]] = None
) -> Optional[str]:
    # Try mapping from active.members.json by name first
    id_map, name_map = _get_id_mapping()
    name_key = name.strip().lower()
    if name_key in name_map:
        return name_map[name_key]

    members = _ensure_members_cache(headers)
    for m in members:
        m_name = m.get("name", "")
        if m_name == name or name in m_name:
            current_id = str(m.get("jkt48_member_id") or m.get("member_id", ""))
            # Return legacy ID if mapped, else return current API ID
            return id_map.get(current_id, current_id)
    return None


def get_theater_or_event_detail(
    reference_code: str,
    event_type: str = "SHOW",
    retry: int = 1,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Get theater or event schedule detail from API."""
    try:
        if event_type == "SHOW":
            api_path = "theater-shows"
        elif event_type == "EXCLUSIVE":
            api_path = "exclusives"
            show_id_exclusive = reference_code.split("-")[0]
            reference_code = reference_code.split("-")[1]
        else:
            api_path = "events"
        url = f"https://jkt48.com/api/v1/{api_path}/{reference_code}?lang=id"

        response = request("GET", url, headers=headers or {}, impersonate="chrome")
        response.raise_for_status()
        data = response.json()

        if not data.get("status") or "data" not in data:
            raise Exception("Show detail not found!")

        detail = data["data"]

        theater_data: List[Dict[str, Any]] = []
        member_map: Dict[str, Dict[str, Any]] = {}

        # Date handling
        wib_date = datetime.now()
        try:
            utc_date_str = detail.get("date", "").replace("Z", "+00:00")
            if not "+" in utc_date_str and not "-" in utc_date_str[-6:]:
                utc_date_str += "+00:00"
            utc_date = datetime.fromisoformat(utc_date_str)
            wib_date = utc_date + timedelta(hours=7)

            start_time_str = detail.get("start_time")
            if start_time_str:
                parts = start_time_str.split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                wib_date = wib_date.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
            wib_date = wib_date.replace(tzinfo=None)
        except Exception:
            pass

        # Get ID and Name mapping (New -> Legacy)
        id_map, name_map = _get_id_mapping()

        members_data = detail.get("jkt48_member", [])
        member_ids = []

        # Map of Current ID -> Legacy ID for this specific show
        show_mapping = {}

        for m in members_data:
            current_id = str(m.get("member_id", "0"))
            m_name = m.get("name", "")

            # Use Legacy ID: priority ID Map -> Name Map -> Current ID
            m_id = (
                id_map.get(current_id)
                or name_map.get(m_name.strip().lower())
                or current_id
            )
            show_mapping[current_id] = m_id

            member_ids.append(m_id)

            member_map[m_id] = {
                "id": m_id,
                "name": m_name,
                "url": f"/member/detail?member={slugify(m_name)}-{current_id}",
            }

        title = detail.get("title", "")
        setlist_id = title.replace(" ", "").lower().strip()
        show_id = (
            str(detail.get("code", reference_code))
            if event_type != "EXCLUSIVE"
            else str(show_id_exclusive)
        )

        member_type = detail.get("jkt48_member_type", "")
        team_id = member_type.lower()
        team_img = ""

        seitansai_ids = []
        bday_names = detail.get("birthday_member_name", [])
        if bday_names:
            for name in bday_names:
                found = False
                for m in members_data:
                    m_name = m.get("name", "")
                    if m_name == name or name in m_name:
                        cur_id = str(m.get("member_id", ""))
                        # Use the mapped Legacy ID from our show_mapping
                        seitansai_ids.append(show_mapping.get(cur_id, cur_id))
                        found = True
                        break

                if not found:
                    global_id = _find_member_id_by_name(name, headers)
                    if global_id:
                        seitansai_ids.append(global_id)

        graduation_ids = []
        if len(member_ids) == 1:
            graduation_ids = member_ids.copy()

        theater_data.append(
            {
                "id": show_id,
                "setlistId": setlist_id,
                "title": title,
                "team": {
                    "id": team_id,
                    "img": team_img,
                },
                "graduationIds": graduation_ids,
                "date": wib_date,
                "memberIds": member_ids,
                "seitansaiIds": seitansai_ids,
                "url": _get_event_url(
                    event_type,
                    show_id if event_type != "EXCLUSIVE" else reference_code,
                    detail.get("link", ""),
                    title,
                ),
                "raw_data": {"detail": detail},
            }
        )

        return {
            "show": theater_data,
            "members": list(member_map.values()),
        }

    except Exception as e:
        if retry > 10:
            print(f"Error fetching {reference_code}: {e}")
            return {"show": [], "members": []}
        time.sleep(1)
        return get_theater_or_event_detail(
            reference_code, event_type, retry + 1, headers
        )
