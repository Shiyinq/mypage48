import asyncio
import os
import sys

# Add project root to pythonpath
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from recorder.src.notify.web_screenshot import capture_web_screenshot

RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")
LIVE_DETAIL_BASE_URL = "https://mypage48.com/jkt48/live/history/live"


async def main():
    # live_id = "510064-1783518537"
    live_id = "ayo-ngobrol-bareng-260708162059"
    output_dir = os.path.join(RECORDINGS_DIR, f"test_{live_id}")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{live_id}_web.png")
    url = f"{LIVE_DETAIL_BASE_URL}/{live_id}"
    print(f"Capturing screenshot for {live_id}")
    print(f"URL: {url}")
    print(f"Output: {output_path}")
    success = await capture_web_screenshot(url, output_path)
    if success:
        print(f"Screenshot saved to {output_path}")
    else:
        print("Failed to capture screenshot")


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
