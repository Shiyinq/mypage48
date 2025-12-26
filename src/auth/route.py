from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_sso.sso.github import GithubSSO
from fastapi_sso.sso.google import GoogleSSO
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.auth.constants import (
    REFRESH_TOKEN_COOKIE_KEY,
    REFRESH_TOKEN_MAX_AGE,
    ErrorCode,
    Info,
)
from src.auth.csrf_service import CSRFService
from src.auth.exceptions import (
    InvalidRefreshTokenError,
    PasswordResetTokenInvalidError,
    RefreshTokenExpiredError,
    SuspiciousActivityError,
    VerificationTokenInvalidError,
)
from src.auth.http_exceptions import EmailNotFoundOrVerified
from src.auth.schemas import (
    EmailVerificationRequest,
    EmailVerificationResponse,
    LogoutResponse,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    Token,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from src.auth.service import AuthService
from src.config import Settings, config
from src.dependencies import (
    get_auth_service,
    get_github_sso,
    get_google_sso,
    get_settings,
    get_user_service,
)
from src.logging_config import create_logger
from src.users.schemas import ProviderUserCreateRequest
from src.users.service import UserService


def _extract_request_info(request: Request):
    user_agent = request.headers.get("user-agent", "")
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    from user_agents import parse as parse_ua

    ua = parse_ua(user_agent)
    device = f"{ua.device.family or 'Unknown'} {ua.os.family or 'Unknown'} {ua.os.version_string or ''}".strip()
    browser = (
        f"{ua.browser.family or 'Unknown'} {ua.browser.version_string or ''}".strip()
    )
    return device, ip, browser, user_agent


def _set_auth_cookies(response: Response, refresh_token: str, config: Settings):
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_KEY,
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_MAX_AGE,
        path="/",
        samesite="lax",
        secure=not config.is_env_dev,
    )

    _set_csrf_cookie(response, config)


def _set_csrf_cookie(response: Response, config: Settings):
    csrf_token = CSRFService.generate_csrf_token()
    response.set_cookie(
        key=CSRFService.CSRF_TOKEN_COOKIE,
        value=csrf_token,
        httponly=False,
        max_age=3600,
        path="/",
        samesite="lax",
        secure=not config.is_env_dev,
    )


def _set_access_token_cookie(response: Response, access_token: str, config: Settings):
    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        max_age=config.access_token_expire_minutes * 60,
        path="/",
        samesite="lax",
        secure=not config.is_env_dev,
    )


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

logger = create_logger("auth", __name__)


@router.post("/auth/signin", response_model=Token)
@limiter.limit(f"{config.auth_requests_per_minute}/minute")
async def signin_with_email_and_password(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    response: Response = None,
    auth_service: AuthService = Depends(get_auth_service),
    config: Settings = Depends(get_settings),
):
    """
    Sign in using email and password. Returns an access token and sets a refresh token cookie.

    Parameters:
        request (Request): FastAPI request object.
        form_data (OAuth2PasswordRequestForm): Form data containing username and password.
        response (Response): FastAPI response object (used to set cookies).

    Returns:
        Token: Access token and token type.
    """

    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    access_token = auth_service.create_access_token(data={"sub": user.userId})

    device, ip, browser, user_agent = _extract_request_info(request)
    refresh_token = await auth_service.register_refresh_token_activity(
        user.userId, device, ip, browser, user_agent
    )

    _set_auth_cookies(response, refresh_token, config)
    _set_access_token_cookie(response, access_token, config)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/refresh", response_model=Token)
async def refresh_access_token(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    config: Settings = Depends(get_settings),
):
    """
    Refresh the access token using a valid refresh token from cookies.

    Parameters:
        request (Request): FastAPI request object (must contain refresh_token cookie).
        response (Response): FastAPI response object.

    Returns:
        Token: New access token and token type.
    """

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        logger.warning("No refresh_token in cookie")
        raise InvalidRefreshTokenError()

    hash_refresh_token = auth_service.hash_token(refresh_token)
    token_data = await auth_service.get_refresh_token(hash_refresh_token)
    if not token_data:
        logger.warning("Token data not found")
        raise InvalidRefreshTokenError()

    device, ip, browser, user_agent = _extract_request_info(request)
    if (
        token_data["device"] != device
        or token_data["ip"] != ip
        or token_data["browser"] != browser
    ):
        logger.warning(f"Device/IP/Browser mismatch user_id={token_data.get('userId')}")
        await auth_service.delete_refresh_token(hash_refresh_token)
        raise SuspiciousActivityError()

    created_at = token_data["createdAt"]
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    if (
        datetime.now(timezone.utc) - created_at
    ).days >= config.refresh_token_max_age_days:
        await auth_service.delete_refresh_token(hash_refresh_token)
        raise RefreshTokenExpiredError()

    await auth_service.update_refresh_token_last_used(hash_refresh_token)
    await auth_service.save_login_history(
        token_data["userId"],
        device,
        ip,
        browser,
        user_agent_raw=user_agent,
    )
    access_token = auth_service.create_access_token(data={"sub": token_data["userId"]})
    _set_access_token_cookie(response, access_token, config)

    _set_csrf_cookie(response, config)

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/google/signin")
async def signin_with_google(google_sso: GoogleSSO = Depends(get_google_sso)):
    """
    Initiate Google OAuth2 sign-in flow. Redirects user to Google login page.

    Returns:
        RedirectResponse: Redirect to Google OAuth2 login.
    """
    with google_sso:
        return await google_sso.get_login_redirect(
            params={"prompt": "consent", "access_type": "offline"}
        )


@router.get("/auth/google/callback")
async def google_auth_callback(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
    google_sso: GoogleSSO = Depends(get_google_sso),
    config: Settings = Depends(get_settings),
):
    """
    Google OAuth2 callback endpoint. Handles user info from Google and issues access token.

    Parameters:
        request (Request): FastAPI request object.
        request (Response): FastAPI response object (used to set cookies).

    Returns:
        RedirectResponse: Redirect to frontend with access token as query param.
    """
    with google_sso:
        user = await google_sso.verify_and_process(request)
        check_user = await auth_service.authenticate_user(
            username_or_email=user.email, provider=user.provider
        )
        if not check_user:
            user_provider = auth_service.extract_user_provider(user)
            user_provider = ProviderUserCreateRequest(**user_provider)
            await user_service.create_user_provider(user_provider)
        access_token = auth_service.create_access_token(data={"sub": user.email})

        device, ip, browser, user_agent = _extract_request_info(request)
        refresh_token = await auth_service.register_refresh_token_activity(
            user.email, device, ip, browser, user_agent
        )

        _set_auth_cookies(response, refresh_token, config)
        _set_access_token_cookie(response, access_token, config)
        redirect_url = f"{config.frontend_url}/auth/callback"
        return RedirectResponse(url=redirect_url, headers=response.headers)


@router.get("/auth/github/signin")
async def signin_with_github(github_sso: GithubSSO = Depends(get_github_sso)):
    """
    Initiate GitHub OAuth2 sign-in flow. Redirects user to GitHub login page.

    Returns:
        RedirectResponse: Redirect to GitHub OAuth2 login.
    """
    with github_sso:
        return await github_sso.get_login_redirect()


@router.get("/auth/github/callback")
async def github_auth_callback(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
    github_sso: GithubSSO = Depends(get_github_sso),
    config: Settings = Depends(get_settings),
):
    """
    GitHub OAuth2 callback endpoint. Handles user info from GitHub and issues access token.

    Parameters:
        request (Request): FastAPI request object.
        request (Response): FastAPI response object (used to set cookies).

    Returns:
        RedirectResponse: Redirect to frontend with access token as query param.
    """
    with github_sso:
        user = await github_sso.verify_and_process(request)
        check_user = await auth_service.authenticate_user(
            username_or_email=user.email, provider=user.provider
        )
        if not check_user:
            user_provider = auth_service.extract_user_provider(user)
            user_provider = ProviderUserCreateRequest(**user_provider)
            await user_service.create_user_provider(user_provider)
        access_token = auth_service.create_access_token(data={"sub": user.email})

        device, ip, browser, user_agent = _extract_request_info(request)
        refresh_token = await auth_service.register_refresh_token_activity(
            user.email, device, ip, browser, user_agent
        )

        _set_auth_cookies(response, refresh_token, config)
        _set_access_token_cookie(response, access_token, config)
        redirect_url = f"{config.frontend_url}/auth/callback"
        return RedirectResponse(url=redirect_url, headers=response.headers)


@router.post("/auth/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    config: Settings = Depends(get_settings),
):
    """
    Log out the current user by deleting the refresh token cookie and invalidating the token in the database.

    Returns:
        LogoutResponse: Message indicating logout success.
    """

    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await auth_service.delete_refresh_token(refresh_token)
        response.delete_cookie(
            key="refresh_token",
            path="/",
            samesite="lax",
            secure=not config.is_env_dev,
            httponly=True,
        )
    response.delete_cookie(
        key="token",
        path="/",
        samesite="lax",
        secure=not config.is_env_dev,
        httponly=True,
    )
    return LogoutResponse(message=Info.LOGOUT_SUCCESS)


# Email Verification Endpoints
@router.post("/auth/send-verification", response_model=EmailVerificationResponse)
@limiter.limit(f"{config.auth_requests_per_minute}/minute")
async def send_email_verification(
    request: Request,
    request_data: EmailVerificationRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Send a verification email to the user for email verification.

    Parameters:
        request (Request): FastAPI request object.
        request_data (EmailVerificationRequest): Email to send verification to.

    Returns:
        EmailVerificationResponse: Message indicating email sent or error.
    """
    result = await auth_service.resend_verification_email(request_data.email)
    if result:
        return EmailVerificationResponse(message=Info.EMAIL_VERIFICATION_SENT)
    else:
        # Don't reveal if user doesn't exist or is already verified
        raise EmailNotFoundOrVerified()


@router.post("/auth/verify-email", response_model=VerifyEmailResponse)
async def verify_email_endpoint(
    request_data: VerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Verify user's email using the provided token.

    Parameters:
        request_data (VerifyEmailRequest): Contains the verification token.

    Returns:
        VerifyEmailResponse: Message indicating verification result.
    """

    success = await auth_service.verify_email(request_data.token)
    if success:
        return VerifyEmailResponse(message=ErrorCode.EMAIL_VERIFIED_SUCCESS)
    else:
        raise VerificationTokenInvalidError()


# Password Reset Endpoints
@router.post("/auth/forgot-password", response_model=PasswordResetResponse)
@limiter.limit(f"{config.auth_requests_per_minute}/minute")
async def forgot_password(
    request: Request,
    request_data: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Send a password reset email to the user.

    Parameters:
        request (Request): FastAPI request object.
        request_data (PasswordResetRequest): Email to send password reset link to.

    Returns:
        PasswordResetResponse: Message indicating reset email sent.
    """
    await auth_service.create_password_reset_token(request_data.email)

    return PasswordResetResponse(message=ErrorCode.PASSWORD_RESET_SENT)


@router.post("/auth/reset-password", response_model=PasswordResetConfirmResponse)
async def reset_password_endpoint(
    request_data: PasswordResetConfirmRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Reset the user's password using the provided token and new password.

    Parameters:
        request_data (PasswordResetConfirmRequest): Contains token, new password, and confirmation.

    Returns:
        PasswordResetConfirmResponse: Message indicating password reset result.
    """

    success = await auth_service.reset_password(
        request_data.token, request_data.new_password
    )
    if success:
        return PasswordResetConfirmResponse(message=ErrorCode.PASSWORD_RESET_SUCCESS)
    else:
        raise PasswordResetTokenInvalidError()
