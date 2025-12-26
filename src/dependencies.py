from fastapi import BackgroundTasks, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi_sso.sso.github import GithubSSO
from fastapi_sso.sso.google import GoogleSSO

from src.api_keys.repository import ApiKeyRepository
from src.api_keys.service import ApiKeyService
from src.auth.csrf_service import CSRFService
from src.auth.email_service import EmailService
from src.auth.http_exceptions import InvalidCSRFToken, InvalidJWTToken
from src.auth.repository import AuthRepository
from src.auth.schemas import UserCurrent
from src.auth.security_service import SecurityService
from src.auth.service import AuthService
from src.config import Settings, config
from src.database import database_instance
from src.health.service import HealthService
from src.logging_config import create_logger
from src.users.repository import UserRepository
from src.users.service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/signin")
logger = create_logger("dependencies", __name__)


def get_db():
    return database_instance.database


def get_settings() -> Settings:
    return config


def get_email_service(config: Settings = Depends(get_settings)) -> EmailService:
    background_runner = AsyncBackgroundRunner()
    return EmailService(config, background_runner)


def get_api_key_repository(db=Depends(get_db)) -> ApiKeyRepository:
    return ApiKeyRepository(db)


def get_api_key_service(
    repo: ApiKeyRepository = Depends(get_api_key_repository),
    config: Settings = Depends(get_settings),
) -> ApiKeyService:
    background_runner = AsyncBackgroundRunner()
    return ApiKeyService(repo, background_runner, config)


def get_user_repository(db=Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_auth_repository(db=Depends(get_db)) -> AuthRepository:
    return AuthRepository(db)


from src.infrastructure import AsyncBackgroundRunner


def get_security_service(
    auth_repo: AuthRepository = Depends(get_auth_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    email_service: EmailService = Depends(get_email_service),
    config: Settings = Depends(get_settings),
) -> SecurityService:
    background_runner = AsyncBackgroundRunner()
    return SecurityService(
        auth_repo, user_repo, email_service, background_runner, config
    )


def get_auth_service(
    auth_repo: AuthRepository = Depends(get_auth_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    security_service: SecurityService = Depends(get_security_service),
    email_service: EmailService = Depends(get_email_service),
    config: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(auth_repo, user_repo, security_service, email_service, config)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
    security_service: SecurityService = Depends(get_security_service),
    email_service: EmailService = Depends(get_email_service),
    config: Settings = Depends(get_settings),
) -> UserService:
    return UserService(user_repo, security_service, email_service, config)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
    auth_service: AuthService = Depends(get_auth_service),
    background_tasks: BackgroundTasks = None,
    config: Settings = Depends(get_settings),
):
    if token.startswith(config.api_key_prefix):
        try:
            user = await api_key_service.validate_api_key(token)
            return UserCurrent(**user)
        except Exception as e:
            logger.warning(f"API Key validation failed: {str(e)}")
            raise InvalidJWTToken()  # Re-raise as 401 for consistency

    token_data = auth_service.verify_access_token(token)
    user = await auth_service.get_user(username_or_email=token_data.username)
    if user is None:
        logger.warning("User not found for provided token")
        raise InvalidJWTToken()
    return UserCurrent(**user.model_dump())


def require_csrf_protection(request: Request, config: Settings = Depends(get_settings)):
    if request.method == "OPTIONS":
        return True

    if request.headers.get("authorization") and request.headers.get(
        "authorization"
    ).startswith(f"Bearer {config.api_key_prefix}"):
        return True

    if config.is_env_dev:
        referer = request.headers.get("referer", "")
        sec_fetch_site = request.headers.get("sec-fetch-site", "")
        if (
            referer.startswith("http://localhost:8000/docs")
            or referer.startswith("http://localhost:8000/redoc")
        ) and sec_fetch_site == "same-origin":
            return True

        user_agent = request.headers.get("user-agent", "").lower()
        if "postman" in user_agent:
            return True

    header_token = request.headers.get(CSRFService.CSRF_TOKEN_HEADER)
    cookie_token = request.cookies.get(CSRFService.CSRF_TOKEN_COOKIE)

    if not CSRFService.validate_csrf_token_string(header_token, cookie_token):
        raise InvalidCSRFToken()
    return True


def get_google_sso(config: Settings = Depends(get_settings)) -> GoogleSSO:
    return GoogleSSO(
        client_id=config.google_client_id,
        client_secret=config.google_client_secret,
        redirect_uri=config.google_redirect_uri,
        allow_insecure_http=config.is_env_dev,
    )


def get_github_sso(config: Settings = Depends(get_settings)) -> GithubSSO:
    return GithubSSO(
        client_id=config.github_client_id,
        client_secret=config.github_client_secret,
        redirect_uri=config.github_redirect_uri,
        allow_insecure_http=config.is_env_dev,
    )


def get_health_service() -> HealthService:
    return HealthService(database_instance)
