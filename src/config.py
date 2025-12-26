from typing import List

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    SECRET_KEY: SecretStr
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_MAX_AGE_DAYS: int = 30

    MONGODB_URI: SecretStr
    DB_NAME: str = "fasmo"

    OAUTHLIB_INSECURE_TRANSPORT: bool = False

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: SecretStr
    GOOGLE_REDIRECT_URI: str
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: SecretStr
    GITHUB_REDIRECT_URI: str

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

    LOG_LEVEL: str = "INFO"
    LOG_DESTINATION: str = "console"
    LOG_PATH: str = "/var/log/fasmo/"

    API_KEY_PREFIX: str = "ffk_"
    DB_MAX_POOL_SIZE: int = 50
    MAX_UPLOAD_SIZE_BYTES: int = 1_048_576  # 1 MB

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=True
    )

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


config = Settings()
