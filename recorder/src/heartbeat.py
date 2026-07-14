import asyncio
import logging

import httpx

logger = logging.getLogger("heartbeat")


async def run_heartbeat(config, mode: str, stop_event: asyncio.Event):
    """
    Background task to ping the Backend API heartbeat endpoint.
    """
    api_url = f"{config.api_base_url}/health/recorder"

    headers = {}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    payload = {
        "mode": mode,
        "bot_token": config.telegram_bot_token if config.telegram_bot_token else None,
        "chat_id": config.telegram_chat_id if config.telegram_chat_id else None,
    }

    logger.info("Starting Recorder Heartbeat task (Mode: %s)...", mode)

    while not stop_event.is_set():
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(api_url, json=payload, headers=headers)
                if not resp.is_success:
                    logger.error(
                        "Heartbeat ping failed: %s - %s", resp.status_code, resp.text
                    )
                else:
                    logger.debug("Heartbeat ping successful.")
        except Exception as e:
            logger.error("Heartbeat ping exception: %s", e)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=config.heartbeat_interval)
        except asyncio.TimeoutError:
            pass
