import time
from typing import Optional

from src.link_resolver.constants import CACHE_MAX_ENTRIES, CACHE_TTL_SECONDS


class LinkResolverRepository:
    """In-memory TTL cache of resolved links.

    The resolver is otherwise stateless; this cache keeps repeated views of the
    same short link from hitting TikTok/Spotify again, which also avoids their
    rate limits. It is intentionally process-local.
    """

    def __init__(
        self,
        max_entries: int = CACHE_MAX_ENTRIES,
        ttl_seconds: int = CACHE_TTL_SECONDS,
    ):
        self._items: dict[str, tuple[str, float]] = {}
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[str]:
        entry = self._items.get(key)
        if not entry:
            return None

        value, expires_at = entry
        if expires_at < time.time():
            self._items.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str) -> None:
        if len(self._items) >= self._max_entries:
            # Dicts keep insertion order, so the first key is the oldest.
            self._items.pop(next(iter(self._items)), None)
        self._items[key] = (value, time.time() + self._ttl_seconds)

    def clear(self) -> None:
        self._items.clear()
