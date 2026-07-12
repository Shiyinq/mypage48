from fastapi import Request
from slowapi import Limiter

from src.config import config


def get_real_ip(request: Request) -> str:
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    if not hasattr(request, "client") or not request.client:
        return "127.0.0.1"
    return request.client.host


limiter = Limiter(
    key_func=get_real_ip,
    default_limits=[f"{config.default_requests_per_minute}/minute"],
)
