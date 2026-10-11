from fastapi import APIRouter, Depends, Request

from src.dependencies import get_link_resolver_service
from src.limiter import limiter
from src.link_resolver.schemas import ResolveLinkRequest, ResolveLinkResponse
from src.link_resolver.service import LinkResolverService

router = APIRouter()


@router.post("/resolve", response_model=ResolveLinkResponse)
@limiter.limit("30/minute", override_defaults=True)
async def resolve_link(
    request: Request,
    body: ResolveLinkRequest,
    service: LinkResolverService = Depends(get_link_resolver_service),
):
    """Resolve an allow-listed short link (TikTok/Spotify) to its canonical URL.

    Any host outside the allow list is rejected, so the endpoint cannot be used
    to reach arbitrary addresses.
    """
    return ResolveLinkResponse(url=await service.resolve(body.url))
