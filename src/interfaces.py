from typing import Any, Callable, Protocol


class BackgroundTaskRunner(Protocol):
    def add_task(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Add a task to be run in the background."""
        ...
