from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import config

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{config.default_requests_per_minute}/minute"],
)
