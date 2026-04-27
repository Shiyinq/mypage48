import hashlib
import math
import re
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


def cleanse_image_url(url: Optional[str]) -> Optional[str]:
    """
    Strip API base URL, Storage endpoint, and signatures from a storage URL to get the internal path.
    Example: http://localhost:8080/api/storage/m/ticket/xyz.png?expires=...
    becomes: ticket/xyz.png
    """
    if not url:
        return url

    # Return data URLs as is
    if url.startswith("data:"):
        return url

    if not url.startswith(("http:", "https:")):
        return url

    proxy_match = re.search(
        r"/storage/m/((journal|ticket|twoshot|avatar|member|setlist)/[^?\s]+)", url
    )
    if proxy_match:
        return proxy_match.group(1)

    # Handle the /media/ paths used by members and setlists
    media_match = re.search(r"/((media/(jkt48-member|setlists)/)[^?\s]+)", url)
    if media_match:
        return media_match.group(1)

    try:
        parsed = urlparse(url)
        path = parsed.path.lstrip("/")
        if path.startswith(f"{config.storage_bucket}/"):
            return path[len(config.storage_bucket) + 1 :]
    except Exception:
        pass

    return url


def cleanse_image_markdown(content: Optional[str]) -> Optional[str]:
    """
    Find storage proxy URLs in markdown and replace with relative internal paths.
    """
    if not content:
        return content

    # Regex to detect internal storage paths in markdown: ![](journal/abc.png)
    # Handles both relative paths and full proxy URLs
    pattern = re.compile(
        r"!\[(.*?)\]\((?:https?://[^/)]+/(?:[^/)]+/)*?)?((journal|ticket|twoshot|avatar)/[^?\s)]+)(?:\?[^)\s]*)?\)"
    )

    def replace_path(match):
        alt_text = match.group(1)
        internal_path = match.group(2)
        return f"![{alt_text}]({internal_path})"

    return pattern.sub(replace_path, content)


def resolve_minio_public_url(url: str) -> str:
    """Replace internal storage host with public URL if configured."""
    if not config.storage_public_url:
        return url

    internal_host = config.storage_endpoint
    public_url = config.storage_public_url

    # Extract only the host:port part from public_url if it contains http://
    public_host = public_url
    if "://" in public_url:
        public_host = public_url.split("://")[1]

    # For R2, sometimes the internal host is already the public one
    if internal_host == public_host:
        return url

    return url.replace(internal_host, public_host)
