import os
from typing import Dict, Optional

from curl_cffi import requests

FLARESOLVERR_URL = os.getenv("FLARESOLVERR_URL", "http://localhost:8191/v1")


def get_cookies_via_flaresolverr(
    url: str, proxy_url: str = FLARESOLVERR_URL
) -> Optional[Dict[str, str]]:
    """
    Get cookies from FlareSolverr for a given URL.
    """
    try:
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000,
        }

        headers = {"Content-Type": "application/json"}

        # Use simple request to talk to FlareSolverr API
        # No impersonate needed for internal API
        response = requests.post(proxy_url, json=payload, headers=headers, timeout=65)
        response.raise_for_status()

        data = response.json()

        if data.get("status") == "ok":
            solution = data.get("solution", {})
            return {
                "cookies": _format_cookies(solution.get("cookies", [])),
                "user_agent": solution.get("userAgent", ""),
            }
        else:
            print(f"FlareSolverr error: {data}")
            return None

    except Exception as e:
        print(f"FlareSolverr connection failed: {e}")
        return None


def _format_cookies(cookies_list: list) -> str:
    """Format cookies list into a cookie string."""
    parts = []
    for c in cookies_list:
        name = c.get("name")
        value = c.get("value")
        if name and value:
            parts.append(f"{name}={value}")
    return "; ".join(parts)
