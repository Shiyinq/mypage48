class AllowedHosts:
    """Hosts the resolver is allowed to talk to.

    This is the core SSRF guard: a request is only ever issued to one of these
    domains, and any redirect that leaves the set is rejected before a socket is
    opened. Everything else a user could paste is refused up front.
    """

    # Short links accepted as input (they carry no post/track id on their own).
    SOURCES = frozenset(
        {
            "vm.tiktok.com",
            "vt.tiktok.com",
            "spotify.link",
            "tiktok.com",
            "www.tiktok.com",
        }
    )

    # Canonical hosts a short link may redirect to.
    TARGETS = frozenset(
        {
            "vm.tiktok.com",
            "vt.tiktok.com",
            "spotify.link",
            "tiktok.com",
            "www.tiktok.com",
            "m.tiktok.com",
            "open.spotify.com",
        }
    )

    # `tiktok.com`/`www.tiktok.com` are only accepted for the `/t/<code>` share
    # links. Canonical `/@user/video/...` links are parsed on the client already.
    TIKTOK_BARE = frozenset({"tiktok.com", "www.tiktok.com"})


MAX_REDIRECTS = 3
REQUEST_TIMEOUT_SECONDS = 8.0
MAX_URL_LENGTH = 2048
MAX_BODY_BYTES = 64 * 1024
CACHE_TTL_SECONDS = 6 * 60 * 60
CACHE_MAX_ENTRIES = 512

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

# Path prefix of TikTok's `tiktok.com/t/<code>` share links.
TIKTOK_SHORT_PATH_PREFIX = "/t/"


class Info:
    RESOLVED = "Link resolved."


class ErrorCode:
    INVALID_LINK = "This link is not supported."
    RESOLVE_FAILED = "Could not resolve the link."


class DomainErrorCode:
    INVALID_LINK = "Invalid or unsupported link."
    RESOLVE_FAILED = "Failed to resolve link."
