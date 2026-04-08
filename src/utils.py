import hashlib
import math
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from password_validator import PasswordValidator

from src.config import config


def pagination(total: int, page: int, limit: int) -> Dict[str, Any]:
    total_pages = math.ceil(total / limit)
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

    return {
        "page": page,
        "limit": limit,
        "prevPage": prev_page,
        "nextPage": next_page,
        "totalPage": total_pages,
    }


def pagination_aggregate(page: int, limit: int) -> Dict[str, Any]:
    skip = limit * (page - 1)
    return {
        "metadata": [
            {"$count": "totalData"},
            {
                "$project": {
                    "totalData": 1,
                    "totalPage": {
                        "$toInt": {"$ceil": {"$divide": ["$totalData", limit]}}
                    },
                    "previousPage": {
                        "$cond": {
                            "if": {"$lte": [page, 1]},
                            "then": None,
                            "else": {"$subtract": [page, 1]},
                        }
                    },
                    "currentPage": {
                        "$cond": {
                            "if": {"$eq": [page, 1]},
                            "then": 1,
                            "else": {"$toInt": {"$ceil": {"$divide": [page, 1]}}},
                        }
                    },
                    "nextPage": {
                        "$cond": {
                            "if": {
                                "$lte": [
                                    {"$add": [page, 1]},
                                    {
                                        "$toInt": {
                                            "$ceil": {"$divide": ["$totalData", limit]}
                                        }
                                    },
                                ]
                            },
                            "then": {"$add": [page, 1]},
                            "else": None,
                        }
                    },
                }
            },
        ],
        "data": [{"$skip": skip}, {"$limit": limit}],
    }


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength:
    - Min 8 chars, Max 64 chars
    - At least one uppercase
    - At least one lowercase
    - At least one digit
    - At least one symbol
    - No spaces
    """
    password_rules = PasswordValidator()
    password_rules.min(8).max(
        64
    ).has().uppercase().has().lowercase().has().digits().has().symbols().no().spaces()
    return password_rules.validate(password)


def clean_image_url(url: Optional[str]) -> Optional[str]:
    """Strip MinIO endpoint and bucket from URL to store only relative path."""
    if not url:
        return None

    # Return data URLs as is
    if url.startswith("data:"):
        return url

    # If not http(s), assume it's already a path
    if not url.startswith(("http:", "https:")):
        return url

    try:
        parsed = urlparse(url)
        path = parsed.path
        if path.startswith("/"):
            path = path[1:]

        # Check if path starts with bucket
        if path.startswith(f"{config.minio_bucket}/"):
            return path[len(config.minio_bucket) + 1 :]

        return url
    except Exception:
        return url


def resolve_minio_public_url(url: str) -> str:
    """Replace internal MinIO host with public URL if configured."""
    if not config.minio_public_url:
        return url

    internal_host = config.minio_endpoint
    public_url = config.minio_public_url

    # Extract only the host:port part from public_url if it contains http://
    public_host = public_url
    if "://" in public_url:
        public_host = public_url.split("://")[1]

    return url.replace(internal_host, public_host)
