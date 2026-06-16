import json
import os
from typing import Dict

# Use absolute path for cookies.json inside the data directory
# BASE_DIR points to the scraper root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COOKIES_FILE = os.path.join(BASE_DIR, "data", "cookies.json")


def get_config_from_file() -> Dict[str, str]:
    """Read config/cookies from JSON file."""
    if os.path.exists(COOKIES_FILE):
        try:
            with open(COOKIES_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {COOKIES_FILE}: {e}")
    return {}


def save_config_to_file(config: Dict[str, str]):
    """Save config/cookies to JSON file."""
    try:
        with open(COOKIES_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error writing {COOKIES_FILE}: {e}")


def get_cookies_headers() -> Dict[str, str]:
    """Get standard headers with cookies."""
    config = get_config_from_file()
    return {
        "Cookie": config.get("cookies", ""),
        "User-Agent": config.get("user_agent", ""),
    }


def save_cookies_from_response(cookie_data: Dict[str, str]):
    """Save new cookies/UA to file."""
    config = get_config_from_file()
    # Update fields
    if "cookies" in cookie_data:
        config["cookies"] = cookie_data["cookies"]
    if "user_agent" in cookie_data:
        config["user_agent"] = cookie_data["user_agent"]

    save_config_to_file(config)
