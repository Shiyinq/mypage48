import asyncio

import resend

from src.config import Settings
from src.interfaces import BackgroundTaskRunner
from src.logging_config import create_logger

logger = create_logger("email", __name__)

# Setup Resend
# Setup Resend will be done in init or globally?
# Ideally we shouldn't have global side effects on import.
# But for now let's keep the global resend.api_key assignment logic BUT move it to init if we want pure decoupling.
# However, resend is a library with global state.
# Let's injecting config first.


class EmailService:
    def __init__(self, config: Settings, background_tasks: BackgroundTaskRunner = None):
        self.config = config
        self.background_tasks = background_tasks
        resend.api_key = self.config.resend_api_key

    async def _send_email(self, payload: dict):
        try:
            logger.info("Sending email")
            # Run blocking I/O (network request) in thread pool
            await asyncio.to_thread(resend.Emails.send, payload)
            logger.info("Email sent successfully")
        except Exception as e:
            logger.exception(f"Error sending email: {e}")

    async def send_email_verification(self, email: str, token: str, username: str):
        """Send email verification"""
        verification_url = f"{self.config.frontend_url}/auth/verify-email?token={token}"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Verify Your Email</h2>
            <p>Hello {username},</p>
            <p>Thank you for registering with Fasmo. Please verify your email by clicking the button below:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" 
                   style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Verify Email
                </a>
            </div>
            <p>Or copy this link to your browser:</p>
            <p style="word-break: break-all; color: #666;">{verification_url}</p>
            <p>This link will expire in {self.config.email_verification_expire_hours} hours.</p>
            <p>If you did not register with Fasmo, please ignore this email.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">Fasmo</p>
        </div>
        """

        payload = {
            "from": self.config.email_from,
            "to": email,
            "subject": "Verify Your Email - Fasmo",
            "html": html_content,
        }

        if self.background_tasks:
            self.background_tasks.add_task(self._send_email, payload)
        else:
            await self._send_email(payload)

    async def send_password_reset(self, email: str, token: str, username: str):
        """Send password reset email"""
        reset_url = f"{self.config.frontend_url}/reset-password?token={token}"

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Reset Your Password</h2>
            <p>Hello {username},</p>
            <p>We received a request to reset your account password. Please click the button below to create a new password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p>Or copy this link to your browser:</p>
            <p style="word-break: break-all; color: #666;">{reset_url}</p>
            <p>This link will expire in {self.config.password_reset_expire_hours} hour.</p>
            <p>If you did not request a password reset, please ignore this email. Your password will not be changed.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">Fasmo</p>
        </div>
        """

        payload = {
            "from": self.config.email_from,
            "to": email,
            "subject": "Reset Your Password - Fasmo",
            "html": html_content,
        }

        if self.background_tasks:
            self.background_tasks.add_task(self._send_email, payload)
        else:
            await self._send_email(payload)

    async def send_account_locked_notification(
        self, email: str, username: str, lockout_duration: int
    ):
        """Send account locked notification"""
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc3545;">Your Account Has Been Locked</h2>
            <p>Hello {username},</p>
            <p>Your account has been temporarily locked due to too many failed login attempts.</p>
            <p>Your account will be automatically unlocked in {lockout_duration} minutes.</p>
            <p>If you forgot your password, please use the "Forgot Password" feature to reset your password.</p>
            <p>If you believe this is an error, please contact our support team.</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">Fasmo</p>
        </div>
        """

        payload = {
            "from": self.config.email_from,
            "to": email,
            "subject": "Account Locked - Fasmo",
            "html": html_content,
        }

        if self.background_tasks:
            self.background_tasks.add_task(self._send_email, payload)
        else:
            await self._send_email(payload)
