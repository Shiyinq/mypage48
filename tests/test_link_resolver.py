import httpx
import pytest
from starlette.requests import Request

from src.exception_handlers import domain_exception_handler
from src.link_resolver.exceptions import InvalidLinkError, LinkResolveError
from src.link_resolver.repository import LinkResolverRepository
from src.link_resolver.service import LinkResolverService

TIKTOK_CANONICAL = "https://www.tiktok.com/@user/video/7312345678901234567"
SPOTIFY_CANONICAL = "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"


def make_service(handler) -> LinkResolverService:
    return LinkResolverService(
        LinkResolverRepository(), transport=httpx.MockTransport(handler)
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://vm.tiktok.com/ZMabc123/",  # not https
        "https://evil.com/ZMabc123/",  # host not allow-listed
        "https://vm.tiktok.com.evil.com/x",  # lookalike host
        "https://tiktok.com/@user/video/7312345678901234567",  # bare host, not /t/
        # A canonical Spotify link is not a short link, so it is not resolved.
        "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT",
    ],
)
async def test_rejects_disallowed_input(url):
    service = make_service(lambda request: httpx.Response(200))
    with pytest.raises(InvalidLinkError):
        await service.resolve(url)


async def test_follows_redirect_to_canonical():
    def handler(request):
        if request.url.host == "vm.tiktok.com":
            return httpx.Response(301, headers={"location": TIKTOK_CANONICAL})
        return httpx.Response(200, text="")

    service = make_service(handler)
    assert await service.resolve("https://vm.tiktok.com/ZMabc123/") == TIKTOK_CANONICAL


async def test_extracts_canonical_from_redirect_page():
    def handler(request):
        return httpx.Response(
            200,
            text=(
                '<meta http-equiv="refresh" ' f'content="0;url={SPOTIFY_CANONICAL}">'
            ),
        )

    service = make_service(handler)
    assert await service.resolve("https://spotify.link/abc123") == SPOTIFY_CANONICAL


async def test_rejects_redirect_outside_allowlist():
    def handler(request):
        return httpx.Response(302, headers={"location": "https://evil.com/x"})

    service = make_service(handler)
    with pytest.raises(InvalidLinkError):
        await service.resolve("https://vm.tiktok.com/ZMabc123/")


async def test_caches_resolution():
    calls = {"count": 0}

    def handler(request):
        if request.url.host == "vm.tiktok.com":
            calls["count"] += 1
            return httpx.Response(301, headers={"location": TIKTOK_CANONICAL})
        return httpx.Response(200, text="")

    service = make_service(handler)
    first = await service.resolve("https://vm.tiktok.com/ZMabc123/")
    second = await service.resolve("https://vm.tiktok.com/ZMabc123/")

    assert first == second == TIKTOK_CANONICAL
    assert calls["count"] == 1


def make_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/link/resolve",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 12345),
            "root_path": "",
        }
    )


async def test_handler_maps_invalid_link_to_400():
    response = await domain_exception_handler(make_request(), InvalidLinkError())
    assert response.status_code == 400


async def test_handler_maps_resolve_error_to_422():
    response = await domain_exception_handler(make_request(), LinkResolveError())
    assert response.status_code == 422
