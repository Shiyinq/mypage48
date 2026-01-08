from fastapi import BackgroundTasks, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi_sso.sso.github import GithubSSO
from fastapi_sso.sso.google import GoogleSSO

from src.achievements.service import AchievementsService
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
from src.dashboard.service import DashboardService
from src.database import database_instance
from src.health.service import HealthService
from src.infrastructure import AsyncBackgroundRunner
from src.llm.repository import LLMRepository
from src.llm.service import LLMService
from src.logging_config import create_logger
from src.members.repository import MemberRepository
from src.members.service import MemberService
from src.memories.repository import MemoriesRepository
from src.memories.service import MemoriesService
from src.setlists.repository import SetlistsRepository
from src.setlists.service import SetlistsService
from src.storage.repository import StorageRepository
from src.storage.service import StorageService
from src.tickets.repository import TicketsRepository
from src.tickets.service import TicketsService
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





def get_llm_repository(db=Depends(get_db)) -> LLMRepository:
    return LLMRepository(db)


def get_llm_service(
    repo: LLMRepository = Depends(get_llm_repository),
    config: Settings = Depends(get_settings),
) -> LLMService:
    return LLMService(repo, config)


def get_tickets_repository(db=Depends(get_db)) -> TicketsRepository:
    return TicketsRepository(db)


def get_tickets_service(
    repo: TicketsRepository = Depends(get_tickets_repository),
    config: Settings = Depends(get_settings),
) -> TicketsService:
    return TicketsService(repo, config)


def get_member_repository(db=Depends(get_db)) -> MemberRepository:
    return MemberRepository(db)


def get_member_service(
    repo: MemberRepository = Depends(get_member_repository),
    config: Settings = Depends(get_settings),
) -> MemberService:
    return MemberService(repo, config)


def get_achievements_service(
    tickets_service: TicketsService = Depends(get_tickets_service),
    config: Settings = Depends(get_settings),
) -> AchievementsService:
    return AchievementsService(tickets_service, config)


def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    security_service: SecurityService = Depends(get_security_service),
    email_service: EmailService = Depends(get_email_service),
    config: Settings = Depends(get_settings),
    tickets_service: TicketsService = Depends(get_tickets_service),
    member_service: MemberService = Depends(get_member_service),
    achievements_service: AchievementsService = Depends(get_achievements_service),
) -> UserService:
    return UserService(
        repo,
        security_service,
        email_service,
        config,
        tickets_service,
        member_service,
        achievements_service,
    )


def get_dashboard_service(
    tickets_repo: TicketsRepository = Depends(get_tickets_repository),
    config: Settings = Depends(get_settings),
) -> DashboardService:
    return DashboardService(tickets_repo, config)


def get_memories_repository(db=Depends(get_db)) -> MemoriesRepository:
    return MemoriesRepository(db)


def get_memories_service(
    repo: MemoriesRepository = Depends(get_memories_repository),
    config: Settings = Depends(get_settings),
) -> MemoriesService:
    return MemoriesService(repo, config)


def get_setlists_repository(db=Depends(get_db)) -> SetlistsRepository:
    return SetlistsRepository(db)


def get_setlists_service(
    repo: SetlistsRepository = Depends(get_setlists_repository),
    config: Settings = Depends(get_settings),
) -> SetlistsService:
    return SetlistsService(repo, config)


def get_storage_repository(
    config: Settings = Depends(get_settings),
) -> StorageRepository:
    return StorageRepository(config)


def get_storage_service(
    repo: StorageRepository = Depends(get_storage_repository),
    config: Settings = Depends(get_settings),
) -> StorageService:
    return StorageService(repo, config)


def get_health_service(
    storage_repo: StorageRepository = Depends(get_storage_repository),
) -> HealthService:
    return HealthService(database_instance, storage_repo)
