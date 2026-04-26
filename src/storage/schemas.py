from typing import Literal, Optional

from pydantic import BaseModel

ImageCategory = Literal["ticket", "twoshot", "avatar", "journal", "member", "setlist"]


class ImageUploadRequest(BaseModel):
    image: str  # base64 encoded
    category: ImageCategory
    slug: Optional[str] = None


class ImageUploadResponse(BaseModel):
    filename: str
    url: str
    url_medium: Optional[str] = None
    url_small: Optional[str] = None
    blurHash: Optional[str] = None


class PresignedUrlResponse(BaseModel):
    url: str
    expires_in: int


class BatchPresignedUrlRequest(BaseModel):
    filenames: list[str]


class BatchPresignedUrlResponse(BaseModel):
    urls: dict[str, str]  # filename -> presigned_url
    expires_in: int
