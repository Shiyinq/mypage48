import logging

log = logging.getLogger("theater")


async def capture_html_screenshot(
    html_content: str, output_path: str, wait_ms: int = 1000
) -> bool:
    """Capture a screenshot of raw HTML content using Playwright."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log.warning("Playwright not installed. Skipping HTML screenshot.")
        return False

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    page = await browser.new_page(
                        viewport={"width": 800, "height": 1000},
                        device_scale_factor=1.5,
                    )
                    log.info(
                        "Capturing HTML screenshot (attempt %d/%d)",
                        attempt,
                        max_retries,
                    )

                    await page.set_content(html_content, wait_until="load")

                    # Force evaluate height
                    full_height = await page.evaluate(
                        """
                        () => {
                            const body = document.body;
                            const html = document.documentElement;
                            return Math.max(
                                body.scrollHeight, body.offsetHeight,
                                html.clientHeight, html.scrollHeight, html.offsetHeight
                            );
                        }
                        """
                    )

                    await page.set_viewport_size({"width": 800, "height": full_height})
                    await page.wait_for_timeout(wait_ms)

                    await page.screenshot(
                        path=output_path, type="jpeg", quality=80, full_page=True
                    )
                    log.info("HTML Screenshot saved successfully")
                    return True
                finally:
                    await browser.close()
        except Exception as e:
            log.warning(
                "HTML Screenshot attempt %d/%d failed: %s", attempt, max_retries, e
            )
            if attempt < max_retries:
                import asyncio

                await asyncio.sleep(2)

    log.error("Failed to capture HTML screenshot after %d attempts", max_retries)
    return False
