from typing import Literal

from pydantic import BaseModel


ImageCategory = Literal["ticket", "twoshot", "avatar"]


class ImageUploadRequest(BaseModel):
    image: str  # base64 encoded
    category: ImageCategory


class ImageUploadResponse(BaseModel):
    filename: str
    url: str


class PresignedUrlResponse(BaseModel):
    url: str
    expires_in: int
