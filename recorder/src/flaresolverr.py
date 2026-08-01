import json
import logging
import os
from typing import Dict

from curl_cffi.requests import AsyncSession

log = logging.getLogger("theater")

# We use the same theater_dir for the cookies state
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKIES_FILE = os.path.join(BASE_DIR, "theater", "flaresolverr_cookies.json")


def get_flaresolverr_config() -> Dict[str, str]:
    """Read config/cookies from JSON file."""
    if os.path.exists(COOKIES_FILE):
        try:
            with open(COOKIES_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"Error reading {COOKIES_FILE}: {e}")
    return {}


def save_flaresolverr_config(config: Dict[str, str]):
    """Save config/cookies to JSON file."""
    try:
        with open(COOKIES_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        log.warning(f"Error writing {COOKIES_FILE}: {e}")


def get_cookies_headers() -> Dict[str, str]:
    """Get standard headers with cookies."""
    config = get_flaresolverr_config()
    return {
        "Cookie": config.get("cookies", ""),
        "User-Agent": config.get("user_agent", ""),
    }


def _format_cookies(cookies_list: list) -> str:
    """Format cookies list into a cookie string."""
    parts = []
    for c in cookies_list:
        name = c.get("name")
        value = c.get("value")
        if name and value:
            parts.append(f"{name}={value}")
    return "; ".join(parts)


async def refresh_cookies_via_flaresolverr(url: str, proxy_url: str) -> bool:
    """
    Get cookies from FlareSolverr for a given URL and save them to disk.
    Returns True if successful.
    """
    try:
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000,
        }
        headers = {"Content-Type": "application/json"}

        # We must use AsyncSession to not block the recorder loop
        async with AsyncSession(timeout=65.0) as client:
            response = await client.post(proxy_url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get("status") == "ok":
                solution = data.get("solution", {})
                new_config = {
                    "cookies": _format_cookies(solution.get("cookies", [])),
                    "user_agent": solution.get("userAgent", ""),
                }
                save_flaresolverr_config(new_config)
                log.info("FlareSolverr successfully fetched new cookies.")
                return True
            else:
                log.warning(f"FlareSolverr error: {data}")
                return False
    except Exception as e:
        log.warning(f"FlareSolverr connection failed: {e}")
        return False


async def fetch_with_retry(
    client: AsyncSession,
    method: str,
    url: str,
    proxy_url: str,
    use_flaresolverr: bool = False,
    **kwargs,
):
    """
    Make a request. If 403, retry once by refreshing cookies via FlareSolverr.
    """
    config = get_flaresolverr_config()
    headers = kwargs.pop("headers", {})
    if config.get("cookies"):
        headers["Cookie"] = config["cookies"]
    if config.get("user_agent"):
        headers["User-Agent"] = config["user_agent"]

    kwargs["headers"] = headers

    # Prevent old cookies from overriding our explicitly injected Cookie header
    if hasattr(client, "cookies"):
        client.cookies.clear()

    resp = await client.request(method, url, **kwargs)
    if resp.status_code != 403 or not use_flaresolverr:
        return resp

    log.info(f"Got 403 for {url}. Refreshing cookies via FlareSolverr...")
    success = await refresh_cookies_via_flaresolverr("https://jkt48.com", proxy_url)
    if success:
        config = get_flaresolverr_config()
        if config.get("cookies"):
            headers["Cookie"] = config["cookies"]
        if config.get("user_agent"):
            headers["User-Agent"] = config["user_agent"]

        kwargs["headers"] = headers
        kwargs["impersonate"] = "chrome"
        log.info(f"Retrying request for {url}...")
        async with AsyncSession(
            timeout=kwargs.get("timeout", 30.0), impersonate="chrome"
        ) as retry_client:
            return await retry_client.request(method, url, **kwargs)

    return resp
