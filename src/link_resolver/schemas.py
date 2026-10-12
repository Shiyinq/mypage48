from pydantic import BaseModel, Field


class ResolveLinkRequest(BaseModel):
    """A short link the client wants resolved to its canonical URL."""

    url: str = Field(..., min_length=1, max_length=2048)


class ResolveLinkResponse(BaseModel):
    """The canonical URL the short link points at."""

    url: str
