import asyncio
from typing import Any, Callable

from src.interfaces import BackgroundTaskRunner
from src.logging_config import create_logger

logger = create_logger("async_runner", __name__)


class AsyncBackgroundRunner(BackgroundTaskRunner):
    """
    Implementation of BackgroundTaskRunner that uses asyncio.create_task
    to fire and forget tasks immediately, ignoring FastAPI's response cycle.
    This is useful when tasks must run even if the request fails (exceptions).
    """

    def add_task(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        async def wrapper():
            try:
                if asyncio.iscoroutinefunction(func):
                    await func(*args, **kwargs)
                else:
                    await asyncio.to_thread(func, *args, **kwargs)
            except Exception as e:
                logger.exception(f"Background task failed: {e}")

        asyncio.create_task(wrapper())
