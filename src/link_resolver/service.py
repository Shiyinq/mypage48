import re
from typing import Optional
from urllib.parse import urljoin, urlsplit

import httpx

from src.link_resolver.constants import (
    MAX_BODY_BYTES,
    MAX_REDIRECTS,
    MAX_URL_LENGTH,
    REQUEST_TIMEOUT_SECONDS,
    TIKTOK_SHORT_PATH_PREFIX,
    USER_AGENT,
    AllowedHosts,
)
from src.link_resolver.exceptions import InvalidLinkError, LinkResolveError
from src.link_resolver.repository import LinkResolverRepository
from src.logging_config import create_logger

logger = create_logger("link_resolver_service", __name__)

_REDIRECT_STATUSES = {301, 302, 303, 307, 308}

# Canonical URLs we accept out of a redirect page body. Used for links that
# redirect with a meta refresh / JS page instead of a plain 3xx.
_CANONICAL_PATTERNS = (
    re.compile(
        r"https://(?:www\.|m\.)?tiktok\.com/@[A-Za-z0-9_.]{1,30}"
        r"/(?:video|photo)/\d{6,25}"
    ),
    re.compile(
        r"https://open\.spotify\.com/(?:intl-[a-z]{2}/)?"
        r"(?:track|album|playlist|episode|artist|show)/[A-Za-z0-9]{22}"
    ),
)


class LinkResolverService:
    """Turn an allow-listed short link into its canonical URL.

    Only the hosts in `AllowedHosts` are ever fetched, and every redirect is
    checked against the same set, so a user cannot make the server reach an
    arbitrary (internal) address.
    """

    def __init__(
        self,
        repository: LinkResolverRepository,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.repository = repository
        # Injectable for tests; production leaves it None (real sockets).
        self.transport = transport

    async def resolve(self, url: str) -> str:
        url = url.strip()
        if not url or len(url) > MAX_URL_LENGTH:
            raise InvalidLinkError()

        self._validate_input(url)

        cached = self.repository.get(url)
        if cached:
            return cached

        final_url = await self._follow(url)
        self._validate_hop(final_url)

        self.repository.set(url, final_url)
        return final_url

    async def _follow(self, url: str) -> str:
        current = url
        seen = {current}
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers=headers,
            transport=self.transport,
        ) as client:
            for _ in range(MAX_REDIRECTS + 1):
                body = ""
                try:
                    async with client.stream("GET", current) as response:
                        status = response.status_code
                        location = response.headers.get("location")

                        if status in _REDIRECT_STATUSES and location:
                            next_url = urljoin(current, location)
                            self._validate_hop(next_url)
                            if next_url in seen:
                                raise LinkResolveError()
                            seen.add(next_url)
                            current = next_url
                            continue

                        if status >= 400:
                            raise InvalidLinkError()

                        # A 200 page may still redirect via meta refresh / JS.
                        body = await self._read_prefix(response)
                except httpx.HTTPError as exc:
                    logger.warning("Link resolve request failed: %s", exc)
                    raise LinkResolveError() from exc

                canonical = self._extract_canonical(body)
                if canonical:
                    self._validate_hop(canonical)
                    return canonical
                return current

        raise LinkResolveError()

    async def _read_prefix(self, response: httpx.Response) -> str:
        """Read at most `MAX_BODY_BYTES` so a huge page cannot be pulled in."""
        chunks: list[bytes] = []
        total = 0
        async for chunk in response.aiter_bytes():
            chunks.append(chunk)
            total += len(chunk)
            if total >= MAX_BODY_BYTES:
                break
        return b"".join(chunks)[:MAX_BODY_BYTES].decode("utf-8", errors="ignore")

    def _extract_canonical(self, body: str) -> Optional[str]:
        if not body:
            return None
        text = body.replace("&amp;", "&")
        for pattern in _CANONICAL_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(0)
        return None

    def _validate_common(self, url: str) -> None:
        parts = urlsplit(url)
        if parts.scheme != "https":
            raise InvalidLinkError()
        if parts.username or parts.password:
            raise InvalidLinkError()
        if parts.port not in (None, 443):
            raise InvalidLinkError()
        if not parts.hostname:
            raise InvalidLinkError()

    def _validate_input(self, url: str) -> None:
        self._validate_common(url)
        host = (urlsplit(url).hostname or "").lower()
        if host not in AllowedHosts.SOURCES:
            raise InvalidLinkError()
        if host in AllowedHosts.TIKTOK_BARE:
            if not urlsplit(url).path.startswith(TIKTOK_SHORT_PATH_PREFIX):
                raise InvalidLinkError()

    def _validate_hop(self, url: str) -> None:
        self._validate_common(url)
        host = (urlsplit(url).hostname or "").lower()
        if host not in AllowedHosts.TARGETS:
            raise InvalidLinkError()
