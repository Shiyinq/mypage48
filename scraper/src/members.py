import json
import os
import time
from typing import Any, Dict, List, Optional, Union

from .agent.browser import request
from .utils import clean_jkt48_url, format_birthdate_id, slugify


def get_members_list(headers: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """Get all members from the API."""
    url = "https://jkt48.com/api/v1/members?lang=id"
    response = request("GET", url, headers=headers or {}, impersonate="chrome")
    response.raise_for_status()
    data = response.json()

    if not data.get("status") or "data" not in data:
        return []

    return data["data"]


def get_member_detail(
    member_id: Union[str, int], headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Get detailed member info from the API."""
    url = f"https://jkt48.com/api/v1/members/{member_id}?lang=id"
    response = request("GET", url, headers=headers or {}, impersonate="chrome")
    response.raise_for_status()
    data = response.json()

    if not data.get("status") or "data" not in data:
        return {}

    return data["data"]


def fetch_and_format_members(headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """Fetch all members from API, merge with legacy data, and format."""

    # Load legacy data for merging
    old_data_map = {}
    current_max_id = 0
    legacy_file = "src/active.members.json"
    if os.path.exists(legacy_file):
        try:
            with open(legacy_file, "r", encoding="utf-8") as f:
                old_list = json.load(f)
                for item in old_list:
                    name_key = item.get("name", "").strip().lower()
                    if name_key:
                        old_data_map[name_key] = item

                    # Track highest numeric ID
                    mid_str = item.get("id", "0")
                    if str(mid_str).isdigit():
                        current_max_id = max(current_max_id, int(mid_str))
        except Exception as e:
            print(f"Warning: Could not load legacy members data: {e}")

    print("Fetching members list...")
    member_list = get_members_list(headers)

    results = []
    processed_names = set()

    for member in member_list:
        m_id = str(member.get("jkt48_member_id", ""))
        if not m_id:
            continue

        time.sleep(0.35)  # Rate limiting
        print(f"Processing Member: {member.get('name', 'Unknown')}")
        member_detail = get_member_detail(m_id, headers)

        # Combine list and detail
        api_data = {**member, **member_detail}
        name = api_data.get("name", "")
        name_key = name.strip().lower()
        processed_names.add(name_key)

        # Get legacy data if exists
        old_item = old_data_map.get(name_key, {})

        # Build refined object
        slug_name = slugify(name)
        m_type = api_data.get("type", "JKT48")

        # Use ID from active.members.json if exists (Legacy JKT48 ID)
        # otherwise use a new unique incrementing ID to avoid collisions (min 310).
        if old_item.get("id"):
            final_id = old_item["id"]
        else:
            current_max_id = max(current_max_id + 1, 310)
            final_id = str(current_max_id)
            print(f"Assigning new Legacy ID {final_id} to {name}")

        href = f"/member/detail?member={slug_name}-{m_id}&type={m_type}"
        img = clean_jkt48_url(
            api_data.get("photo") or api_data.get("photo_1") or old_item.get("img", "")
        )

        refined = {
            "active": True,
            "id": final_id,  # Primary ID for the app (Preserving Legacy JKT48 ID)
            "jkt48_id": m_id,  # Current JKT48 Official Website ID
            "birthdate": format_birthdate_id(api_data.get("birth_date", "")),
            "bloodType": api_data.get("blood_type", "")
            or old_item.get("bloodType", ""),
            "generation": str(old_item.get("generation", "")),
            "height": f"{api_data.get('body_height', '')}cm"
            if api_data.get("body_height")
            else old_item.get("height", ""),
            "horoscope": api_data.get("horoscope", "") or old_item.get("horoscope", ""),
            "href": href,
            "img": img,
            "jiko": old_item.get("jiko", ""),
            "name": name,
            "nickname": api_data.get("nickname", "") or old_item.get("nickname", ""),
            "socials": old_item.get(
                "socials",
                {
                    "idn_app": "",
                    "instagram": f"https://www.instagram.com/{api_data.get('instagram_account', '')}/"
                    if api_data.get("instagram_account")
                    else "",
                    "showroom": "",
                    "threads": "",
                    "tiktok": f"https://www.tiktok.com/@{api_data.get('tiktok_account', '')}/"
                    if api_data.get("tiktok_account")
                    else "",
                    "twitter": f"https://twitter.com/{api_data.get('twitter_account', '')}"
                    if api_data.get("twitter_account")
                    else "",
                },
            ),
            "member_code": api_data.get("code", ""),
            "member_type": m_type,
        }
        results.append(refined)

    # FINAL MERGE: Keep members from active.members.json that are NOT in current API response
    for name_key, old_item in old_data_map.items():
        if name_key not in processed_names:
            print(
                f"Keeping graduated/historical member: {old_item.get('name', 'Unknown')}"
            )
            # Ensure they are marked as inactive
            old_item["active"] = False
            results.append(old_item)

    return results
