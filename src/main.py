import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from src.api import router as api_router
from src.config import config
from src.database import database_instance

if config.oauthlib_insecure_transport:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from src.exception_handlers import (
    detailed_http_exception_handler,
    domain_exception_handler,
)
from src.exceptions import DomainException
from src.http_exceptions import BadRequest, DetailedHTTPException, EntityTooLarge
from src.logging_config import request_id_ctx_var


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database_instance.connect()

    yield

    await database_instance.close()


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{config.default_requests_per_minute}/minute"],
)

app = FastAPI(
    title="Fasmo API",
    openapi_url="/api/openapi.json"
    if config.is_env_dev
    else None,  # Disable docs schema in prod
    docs_url="/docs" if config.is_env_dev else None,  # Disable Swagger UI in prod
    redoc_url="/redoc" if config.is_env_dev else None,  # Disable ReDoc in prod
    debug=config.is_env_dev,  # Enable debug only in dev
    lifespan=lifespan,
)


app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(DetailedHTTPException, detailed_http_exception_handler)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    max_upload_size = config.max_upload_size_bytes
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > max_upload_size:
                raise EntityTooLarge()
        except ValueError:
            raise BadRequest()
    return await call_next(request)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    request_id_ctx_var.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000; includeSubDomains"

    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net blob:; "
            "worker-src 'self' blob:; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "img-src 'self' https://fastapi.tiangolo.com https://cdn.jsdelivr.net https://cdn.redoc.ly data:; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "connect-src 'self'"
        )
    else:
        response.headers[
            "Content-Security-Policy"
        ] = "default-src 'self'; script-src 'self'"

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID",
        "X-CSRF-Token",
    ],
    expose_headers=["X-Request-ID"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

app.include_router(api_router, prefix="/api")
