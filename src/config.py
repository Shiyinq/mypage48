from typing import List, Optional

from pydantic import SecretStr, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    SECRET_KEY: SecretStr
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_MAX_AGE_DAYS: int = 30

    MONGODB_URI: SecretStr
    DB_NAME: str = "mypage48"

    OAUTHLIB_INSECURE_TRANSPORT: bool = False

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: SecretStr
    GOOGLE_REDIRECT_URI: str
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: SecretStr
    GITHUB_CLIENT_SECRET: SecretStr
    GITHUB_REDIRECT_URI: str

    GEMINI_API_KEY: SecretStr

    FRONTEND_URL: str
    ORIGINS: str

    RESEND_API_KEY: SecretStr
    EMAIL_FROM: str = "onboarding@resend.dev"
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_HOURS: int = 1

    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15
    AUTH_REQUESTS_PER_MINUTE: int = 60
    DEFAULT_REQUESTS_PER_MINUTE: int = 120
    LIVE_PROXY_REQUESTS_PER_MINUTE: int = 1500

    LOG_LEVEL: str = "INFO"
    LOG_DESTINATION: str = "console"
    LOG_PATH: str = "/var/log/mypage48/"

    API_KEY_PREFIX: str = "ffk_"
    DB_MAX_POOL_SIZE: int = 50
    MAX_UPLOAD_SIZE_BYTES: int = 10_485_760  # 10 MB

    # Storage Settings (Agnostic S3/R2)
    STORAGE_PROVIDER: str = "minio"  # "minio" or "r2"
    STORAGE_ENDPOINT: str = "localhost:9000"
    STORAGE_ACCESS_KEY: SecretStr = SecretStr("minioadmin")
    STORAGE_SECRET_KEY: SecretStr = SecretStr("minioadmin123")
    STORAGE_BUCKET: str = "mypage48-images"
    STORAGE_SECURE: bool = False
    STORAGE_PUBLIC_URL: Optional[str] = None
    STORAGE_USE_PRESIGNED: bool = False

    API_BASE_URL: str = "http://localhost:8080/api"

    # Analytics (Optional, mainly for frontend build but added here for central config)
    PUBLIC_UMAMI_WEBSITE_ID: Optional[str] = None
    PUBLIC_UMAMI_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=True
    )

    @field_validator("FRONTEND_URL", "API_BASE_URL")
    @classmethod
    def validate_prod_urls(cls, v: str, info):
        # We need to access ENV, but field_validators run per-field.
        # This will be supplemented by model_validator below.
        return v

    @model_validator(mode="after")
    def validate_production_hardening(self) -> "Settings":
        if self.ENV == "prod":
            # 1. Check URLs for localhost
            for field in ["FRONTEND_URL", "API_BASE_URL"]:
                val = getattr(self, field)
                if "localhost" in val or "127.0.0.1" in val:
                    raise ValueError(
                        f"{field} cannot contain 'localhost' or '127.0.0.1' in production. Value was: {val}"
                    )

            # 2. Force MinIO Secure if not explicitly overridden to False
            # (though explicitly False in prod is also suspicious unless behind a very specific internal proxy)
            # For now, let's just warn or nudge.
            if not self.MINIO_SECURE:
                # We could raise an error, but let's allow it if they really know what they are doing (e.g. internal network)
                # but default it to True in our recommended template.
                pass

        return self

    @property
    def is_env_dev(self) -> bool:
        return self.ENV == "dev"

    @computed_field
    @property
    def cors_origins(self) -> List[str]:
        if not self.ORIGINS:
            if self.is_env_dev:
                return [
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:5173",
                ]
            else:
                raise ValueError(
                    "ORIGINS environment variable is required in production"
                )

        origins = [
            origin.strip() for origin in self.ORIGINS.split(",") if origin.strip()
        ]

        if not self.is_env_dev:
            # In production, we assume the subdomains are part of the origins
            for origin in origins:
                if origin == "*":
                    raise ValueError(
                        "Wildcard (*) origins are not allowed in production"
                    )
                if not origin.startswith("https://"):
                    raise ValueError(
                        f"Only HTTPS origins allowed in production: {origin}"
                    )

        return origins

    @property
    def mongo_uri(self) -> str:
        return self.MONGODB_URI.get_secret_value()

    @property
    def db_name(self) -> str:
        return self.DB_NAME

    @property
    def oauthlib_insecure_transport(self) -> bool:
        return self.OAUTHLIB_INSECURE_TRANSPORT

    @computed_field
    @property
    def secret_key(self) -> str:
        secret_value = self.SECRET_KEY.get_secret_value()
        if len(secret_value) < 32:
            if (
                not self.is_env_dev
            ):  # Allow short key in dev for convenience, but strict in prod
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters long in production"
                )
        return secret_value

    @property
    def algorithm(self) -> str:
        allowed_algos = ["HS256", "RS256"]
        algo = self.ALGORITHM or "HS256"  # Default to HS256 if None
        if algo.lower() == "none" or algo not in allowed_algos:
            raise ValueError(
                f"Algorithm {algo} is not allowed. Choose from {allowed_algos}"
            )
        return algo

    @property
    def access_token_expire_minutes(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def refresh_token_max_age_days(self) -> int:
        return self.REFRESH_TOKEN_MAX_AGE_DAYS

    @property
    def google_client_id(self) -> str:
        return self.GOOGLE_CLIENT_ID

    @property
    def google_client_secret(self) -> str:
        return self.GOOGLE_CLIENT_SECRET.get_secret_value()

    @property
    def google_redirect_uri(self) -> str:
        return self.GOOGLE_REDIRECT_URI

    @property
    def github_client_id(self) -> str:
        return self.GITHUB_CLIENT_ID

    @property
    def github_client_secret(self) -> str:
        return self.GITHUB_CLIENT_SECRET.get_secret_value()

    @property
    def github_redirect_uri(self) -> str:
        return self.GITHUB_REDIRECT_URI

    @property
    def gemini_api_key(self) -> str:
        return self.GEMINI_API_KEY.get_secret_value()

    @property
    def frontend_url(self) -> str:
        return self.FRONTEND_URL

    @property
    def resend_api_key(self) -> str:
        return self.RESEND_API_KEY.get_secret_value()

    @property
    def email_from(self) -> str:
        return self.EMAIL_FROM

    @property
    def email_verification_expire_hours(self) -> int:
        return self.EMAIL_VERIFICATION_EXPIRE_HOURS

    @property
    def password_reset_expire_hours(self) -> int:
        return self.PASSWORD_RESET_EXPIRE_HOURS

    @property
    def max_login_attempts(self) -> int:
        return self.MAX_LOGIN_ATTEMPTS

    @property
    def account_lockout_minutes(self) -> int:
        return self.ACCOUNT_LOCKOUT_MINUTES

    @property
    def auth_requests_per_minute(self) -> int:
        return self.AUTH_REQUESTS_PER_MINUTE

    @property
    def default_requests_per_minute(self) -> int:
        return self.DEFAULT_REQUESTS_PER_MINUTE

    @property
    def live_proxy_requests_per_minute(self) -> int:
        return self.LIVE_PROXY_REQUESTS_PER_MINUTE

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @property
    def log_destination(self) -> str:
        return self.LOG_DESTINATION

    @property
    def log_path(self) -> str:
        return self.LOG_PATH

    @property
    def api_key_prefix(self) -> str:
        return self.API_KEY_PREFIX

    @property
    def db_max_pool_size(self) -> int:
        return self.DB_MAX_POOL_SIZE

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_BYTES

    @property
    def storage_provider(self) -> str:
        return self.STORAGE_PROVIDER

    @property
    def storage_endpoint(self) -> str:
        return self.STORAGE_ENDPOINT

    @property
    def storage_access_key(self) -> str:
        return self.STORAGE_ACCESS_KEY.get_secret_value()

    @property
    def storage_secret_key(self) -> str:
        return self.STORAGE_SECRET_KEY.get_secret_value()

    @property
    def storage_bucket(self) -> str:
        return self.STORAGE_BUCKET

    @property
    def storage_secure(self) -> bool:
        return self.STORAGE_SECURE

    @property
    def storage_public_url(self) -> Optional[str]:
        return self.STORAGE_PUBLIC_URL

    @property
    def storage_use_presigned(self) -> bool:
        return self.STORAGE_USE_PRESIGNED

    # Backward compatibility properties (will be removed after full migration)
    @property
    def minio_endpoint(self) -> str:
        return self.STORAGE_ENDPOINT

    @property
    def minio_access_key(self) -> str:
        return self.STORAGE_ACCESS_KEY.get_secret_value()

    @property
    def minio_secret_key(self) -> str:
        return self.STORAGE_SECRET_KEY.get_secret_value()

    @property
    def minio_bucket(self) -> str:
        return self.STORAGE_BUCKET

    @property
    def minio_secure(self) -> bool:
        return self.STORAGE_SECURE

    @property
    def minio_public_url(self) -> Optional[str]:
        return self.STORAGE_PUBLIC_URL

    @property
    def api_base_url(self) -> str:
        return self.API_BASE_URL.rstrip("/")


config = Settings()
