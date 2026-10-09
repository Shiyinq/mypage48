import asyncio
import logging

try:
    from playwright.async_api import async_playwright
except ImportError:  # optional dependency
    async_playwright = None

log = logging.getLogger("notify")

# Wall-clock budget for a single capture attempt. Kept comfortably above the
# sum of the per-operation timeouts (goto 30s + screenshot 60s + fixed waits
# 10s + launch/new_page/evaluate) so normal slowness is never preempted.
_ATTEMPT_TIMEOUT = 210

# Bound on browser shutdown. Without it a wedged Chromium can hang forever.
_CLOSE_TIMEOUT = 10

# Cap the rendered page height. A full-page screenshot at scale factor 2
# allocates roughly width * 2 * height * 2 * 4 bytes, so an unbounded page
# (the CSS override expands every scroll container) can exhaust RAM.
_MAX_PAGE_HEIGHT = 20000


async def capture_web_screenshot(
    url: str, output_path: str, wait_ms: int = 7000
) -> bool:
    """Capture a full-page screenshot of a web page using Playwright.

    Args:
        url: Full URL of the page to screenshot.
        output_path: File path to save the screenshot.
        wait_ms: Extra milliseconds to wait after CSS override for animations.
    """
    if async_playwright is None:
        log.warning("Playwright not installed. Skipping web screenshot.")
        return False

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            await asyncio.wait_for(
                _capture_once(url, output_path, wait_ms, attempt, max_retries),
                timeout=_ATTEMPT_TIMEOUT,
            )
            return True
        except Exception as e:
            log.warning(
                "Screenshot attempt %d/%d failed: %s",
                attempt,
                max_retries,
                e,
            )
            if attempt < max_retries:
                await asyncio.sleep(3)

    log.error("Failed to capture web screenshot after %d attempts", max_retries)
    return False


async def _capture_once(
    url: str, output_path: str, wait_ms: int, attempt: int, max_retries: int
) -> None:
    """Run one capture attempt, raising on failure.

    The caller wraps this in a wall-clock timeout so a wedged Chromium can
    never hold the surrounding task forever.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(
                viewport={"width": 1080, "height": 1920},
                device_scale_factor=2,
                timezone_id="Asia/Jakarta",
            )
            log.info(
                "Capturing web screenshot at %s (attempt %d/%d)",
                url,
                attempt,
                max_retries,
            )
            await page.goto(url, wait_until="load", timeout=30000)

            # Wait for initial DOM and data loading
            await page.wait_for_timeout(3000)

            # Force all elements to expand vertically only
            # Keep horizontal overflow intact to prevent layout stretching
            full_height = await page.evaluate(
                """
                () => {
                    const all = document.querySelectorAll('*');
                    for (const el of all) {
                        const cs = getComputedStyle(el);
                        if (cs.overflow === 'hidden' || cs.overflowY === 'hidden') {
                            el.style.overflowY = 'visible';
                        }
                        if (cs.overflowY === 'auto' || cs.overflowY === 'scroll') {
                            el.style.overflowY = 'visible';
                            el.style.height = 'auto';
                            el.style.flex = 'none';
                        }
                    }
                    document.documentElement.style.height = 'auto';
                    document.documentElement.style.overflowY = 'visible';
                    document.body.style.height = 'auto';
                    document.body.style.overflowY = 'visible';

                    return document.body.scrollHeight;
                }
                """
            )
            full_height = max(1, min(int(full_height), _MAX_PAGE_HEIGHT))
            log.info("Full page height after CSS override: %d", full_height)

            # Resize viewport to match full content height
            await page.set_viewport_size({"width": 1080, "height": full_height})

            # Wait for layout reflow and animations
            await page.wait_for_timeout(wait_ms)
            await page.screenshot(path=output_path, full_page=True, timeout=60000)
            log.info(
                "Screenshot saved successfully (attempt %d/%d)",
                attempt,
                max_retries,
            )
        finally:
            try:
                await asyncio.wait_for(browser.close(), timeout=_CLOSE_TIMEOUT)
            except Exception as e:
                log.warning("browser.close() did not complete cleanly: %s", e)
