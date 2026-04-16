"""
Browser Agent module.
Handles HTTP requests, header management, and automatic retries via FlareSolverr.
"""
import time

from curl_cffi import requests

from .cookies import get_cookies_headers, save_cookies_from_response
from .flaresolverr import get_cookies_via_flaresolverr


def request(method: str, url: str, **kwargs) -> requests.Response:
    """
    Make a request with "Lazy Retry" logic.

    Strategy:
    1. Try request with current local cookies.
    2. If 403 Forbidden is returned:
       a. Call FlareSolverr to solve Cloudflare challenge.
       b. Update local cookies.
       c. Retry request with new cookies.

    NOTE: `curl_cffi` with `impersonate='chrome'` is often strong enough to bypass
    Cloudflare protections on jkt48.com even WITHOUT valid cookies (cf_clearance).
    However, protections may tighten at any time (e.g., during heavy traffic).
    This function implements a "Lazy Retry" strategy to handle both cases efficiently.
    """
    # 1. Prepare headers and Cookies
    config = get_cookies_headers()

    if "headers" not in kwargs:
        kwargs["headers"] = {}

    # Merge config headers (Cookie & User-Agent) into request headers
    # This ensures FlareSolverr's UA and Cookies are always used
    for key, value in config.items():
        if value:
            kwargs["headers"][key] = value

    # Default to chrome impersonation
    if "impersonate" not in kwargs:
        kwargs["impersonate"] = "chrome"

    try:
        # 2. Attempt request
        response = requests.request(method, url, **kwargs)

        # Happy path or non-403 error
        if response.status_code != 403:
            return response

        print(f"Got 403 Forbidden for {url}. Attempting to bypass...")

    except Exception as e:
        print(f"Request failed: {e}")

    # 3. Recovery Logic (FlareSolverr)
    # We use the HOMEPAGE to get cookies because API endpoints often don't trigger challenges
    print("Refreshing cookies via JKT48 Homepage (FlareSolverr)...")
    new_cookies = get_cookies_via_flaresolverr("https://jkt48.com")

    if new_cookies:
        print("Cookies refreshed successfully!")

        # Save cookies and User-Agent to file
        save_cookies_from_response(new_cookies)

        # Re-fetch config and update headers for retry
        new_config = get_cookies_headers()
        for key, value in new_config.items():
            if value:
                kwargs["headers"][key] = value

        # 4. Retry request
        print("Retrying request...")
        time.sleep(1)
        return requests.request(method, url, **kwargs)
    else:
        print("FlareSolverr failed or not available.")

    # If recovery failed, execute request one last time (or return the failed response)
    return requests.request(method, url, **kwargs)
