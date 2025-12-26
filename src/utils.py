import hashlib
import math
from typing import Any, Dict

from password_validator import PasswordValidator


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
    - Min 8 chars, Max 128 chars
    - At least one uppercase
    - At least one lowercase
    - At least one digit
    - At least one symbol
    - No spaces
    """
    password_rules = PasswordValidator()
    password_rules.min(8).max(
        128
    ).has().uppercase().has().lowercase().has().digits().has().symbols().no().spaces()
    return password_rules.validate(password)
