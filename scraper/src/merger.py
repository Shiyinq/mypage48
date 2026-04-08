import glob
import json
import os
from typing import Any, Dict, Optional

from .utils import clean_jkt48_url


def load_reference_members(path: str) -> Dict[str, Dict[str, Any]]:
    """Load reference members and map by ID."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            members = json.load(f)
            return {m["id"]: m for m in members}
    except FileNotFoundError:
        print(f"Warning: Reference file {path} not found.")
        return {}


def format_member(
    member_id: str,
    member_name: str,
    member_url: str,
    ref_member: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Format member object based on reference schema."""
    if ref_member:
        # Clone to avoid modifying original info if reused
        m = ref_member.copy()
        if "_id" in m:
            del m["_id"]
        return m

    # Default structure for missing members
    return {
        "active": False,
        "birthdate": None,
        "bloodType": None,
        "generation": None,
        "height": None,
        "horoscope": None,
        "href": clean_jkt48_url(member_url),  # Use scraped URL as href
        "id": member_id,
        "img": None,
        "jiko": None,
        "name": member_name,  # Use scraped name
        "nickname": None,
        "socials": None,
        "member_type": None,
    }


def merge_data():
    print("Starting data merge...")

    # 1. Collect all events from data/historical/schedule_*.json
    all_events = []
    scraped_members_map = {}  # id -> {name, url}

    historical_dir = "data/schedule"
    file_pattern = os.path.join(historical_dir, "events.schedule.*.json")
    files = glob.glob(file_pattern)

    print(f"Found {len(files)} historical schedule files in {historical_dir}.")

    years = []
    for file_path in files:
        # Extract year from filename: events.schedule.2011.json -> 2011
        try:
            filename = os.path.basename(file_path)
            import re

            match = re.search(r"events\.schedule\.(\d{4})\.json", filename)
            if match:
                years.append(int(match.group(1)))
        except Exception:
            pass

        print(f"Processing {file_path}...")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Append events
                if "events" in data:
                    all_events.extend(data["events"])

                # Collect unique members info from this file
                if "members" in data:
                    for m in data["members"]:
                        if m["id"] not in scraped_members_map:
                            scraped_members_map[m["id"]] = {
                                "name": m.get("name", ""),
                                "url": m.get("url", ""),
                            }
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    if not files:
        print("No files found. Exiting.")
        return

    # Determine year range
    min_year = min(years) if years else "unknown"
    max_year = max(years) if years else "unknown"

    # 2. Sort events by date
    all_events.sort(key=lambda x: x.get("date", ""))

    print(f"Total events found: {len(all_events)}")

    # Resolve active.members.json relative to this file
    base_dir = os.path.dirname(__file__)
    members_path = os.path.join(base_dir, "active.members.json")
    ref_members_map = load_reference_members(members_path)
    final_members = []

    for member_id, info in scraped_members_map.items():
        ref_data = ref_members_map.get(member_id)
        formatted = format_member(member_id, info["name"], info["url"], ref_data)
        final_members.append(formatted)

    # Sort members by ID for consistency
    try:
        final_members.sort(key=lambda x: int(x["id"]))
    except:
        final_members.sort(key=lambda x: x["id"])

    print(f"Total unique members found: {len(final_members)}")

    # 4. Save output
    output_events = os.path.join(
        historical_dir, f"events.schedule_{min_year}_to_{max_year}.json"
    )
    with open(output_events, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)
    print(f"Saved events to {output_events}")

    output_members = os.path.join(
        historical_dir, f"members_{min_year}_to_{max_year}.json"
    )
    with open(output_members, "w", encoding="utf-8") as f:
        json.dump(final_members, f, indent=2, ensure_ascii=False)
    print(f"Saved members to {output_members}")


if __name__ == "__main__":
    merge_data()
