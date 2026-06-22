import asyncio
import html

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
        <div style="background-color: #fdf2f8; padding: 60px 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 28px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.08); border: 1px solid rgba(236, 72, 153, 0.1);">
                <div style="padding: 40px 20px; text-align: center; border-bottom: 1px solid #f1f5f9;">
                    <h1 style="color: #0f172a; margin: 0; font-size: 32px; font-weight: 900; letter-spacing: -0.05em;">MyPage<span style="color: #ef4444;">48</span></h1>
                    <p style="color: #ef4444; margin: 4px 0 0; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.2em;">Official Member Account</p>
                </div>
                <div style="padding: 48px 40px;">
                    <h2 style="color: #ef4444; margin: 0 0 16px; font-size: 28px; font-weight: 900; tracking: -0.02em;">Verify Your Email</h2>
                    <p style="color: #475569; line-height: 1.8; margin: 0 0 24px; font-size: 16px;">Hello <strong>{username}</strong>,</p>
                    <p style="color: #475569; line-height: 1.8; margin: 0 0 40px; font-size: 16px;">Welcome to the family! To activate your digital theater profile and start your journey with MyPage48, please verify your email address below:</p>
                    
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{verification_url}" 
                           style="background-color: #dc2626; color: #ffffff; padding: 22px 48px; text-decoration: none; border-radius: 18px; display: inline-block; font-weight: 800; font-size: 16px; box-shadow: 0 10px 25px -5px rgba(220, 38, 38, 0.4); transition: all 0.2s ease;">
                            Verify My Email
                        </a>
                    </div>
                    
                    <div style="background-color: #f8fafc; padding: 24px; border-radius: 18px; border: 1px dashed #cbd5e1; margin: 40px 0;">
                        <p style="color: #64748b; font-size: 11px; margin: 0 0 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;">Security Backup Link:</p>
                        <p style="word-break: break-all; color: #ef4444; font-size: 13px; margin: 0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-weight: 500;">{verification_url}</p>
                    </div>
                    
                    <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; text-align: center; font-weight: 500;">This link is valid for {self.config.email_verification_expire_hours} hours. <br>If you didn't request this, you can safely ignore this email.</p>
                </div>
                <div style="background-color: #f1f5f9; padding: 32px; text-align: center;">
                    <p style="color: #0f172a; font-weight: 900; font-size: 14px; margin: 0;">MyPage48</p>
                    <p style="color: #64748b; font-size: 11px; margin: 4px 0 0; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Create your digital theater profile</p>
                </div>
            </div>
        </div>
        """

        payload = {
            "from": self.config.email_from,
            "to": email,
            "subject": "Verify Your Email - MyPage48",
            "html": html_content,
        }

        if self.background_tasks:
            self.background_tasks.add_task(self._send_email, payload)
        else:
            await self._send_email(payload)

    async def send_password_reset(self, email: str, token: str, username: str):
        """Send password reset email"""
        reset_url = f"{self.config.frontend_url}/auth/reset-password?token={token}"

        html_content = f"""
        <div style="background-color: #fdf2f8; padding: 60px 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 28px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.08); border: 1px solid rgba(236, 72, 153, 0.1);">
                <div style="padding: 40px 20px; text-align: center; border-bottom: 1px solid #f1f5f9;">
                    <h1 style="color: #0f172a; margin: 0; font-size: 32px; font-weight: 900; letter-spacing: -0.05em;">MyPage<span style="color: #ef4444;">48</span></h1>
                    <p style="color: #ef4444; margin: 4px 0 0; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.2em;">Security Notification</p>
                </div>
                <div style="padding: 48px 40px;">
                    <h2 style="color: #ef4444; margin: 0 0 16px; font-size: 28px; font-weight: 900; tracking: -0.02em;">Reset Your Password</h2>
                    <p style="color: #475569; line-height: 1.8; margin: 0 0 24px; font-size: 16px;">Hello <strong>{username}</strong>,</p>
                    <p style="color: #475569; line-height: 1.8; margin: 0 0 40px; font-size: 16px;">We received a request to reset your password. If this was you, please click the button below to set a new one:</p>
                    
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{reset_url}" 
                           style="background-color: #dc2626; color: #ffffff; padding: 22px 48px; text-decoration: none; border-radius: 18px; display: inline-block; font-weight: 800; font-size: 16px; box-shadow: 0 10px 25px -5px rgba(220, 38, 38, 0.4); transition: all 0.2s ease;">
                            Reset My Password
                        </a>
                    </div>
                    
                    <div style="background-color: #f8fafc; padding: 24px; border-radius: 18px; border: 1px dashed #cbd5e1; margin: 40px 0;">
                        <p style="color: #64748b; font-size: 11px; margin: 0 0 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;">Quick Access Link:</p>
                        <p style="word-break: break-all; color: #ef4444; font-size: 13px; margin: 0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-weight: 500;">{reset_url}</p>
                    </div>
                    
                    <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; text-align: center; font-weight: 500;">This link is valid for {self.config.password_reset_expire_hours} hour. <br>If you didn't request this, ignore this email.</p>
                </div>
                <div style="background-color: #f1f5f9; padding: 32px; text-align: center;">
                    <p style="color: #0f172a; font-weight: 900; font-size: 14px; margin: 0;">MyPage48</p>
                    <p style="color: #64748b; font-size: 11px; margin: 4px 0 0; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Guarding your memories</p>
                </div>
            </div>
        </div>
        """

        payload = {
            "from": self.config.email_from,
            "to": email,
            "subject": "Reset Your Password - MyPage48",
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
        forgot_password_url = f"{self.config.frontend_url}/auth/forgot-password"

        html_content = f"""
        <div style="background-color: #fdf2f8; padding: 60px 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 28px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.08); border: 1px solid rgba(236, 72, 153, 0.1);">
                <div style="padding: 40px 20px; text-align: center; border-bottom: 1px solid #f1f5f9;">
                    <h1 style="color: #0f172a; margin: 0; font-size: 32px; font-weight: 900; letter-spacing: -0.05em;">MyPage<span style="color: #ef4444;">48</span></h1>
                    <p style="color: #ef4444; margin: 4px 0 0; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.2em;">Security Alert</p>
                </div>
                <div style="padding: 48px 40px;">
                    <h2 style="color: #ef4444; margin: 0 0 16px; font-size: 28px; font-weight: 900; tracking: -0.02em;">Account Locked</h2>
                    <p style="color: #475569; line-height: 1.8; margin: 0 0 24px; font-size: 16px;">Hello <strong>{username}</strong>,</p>
                    <p style="color: #475569; line-height: 1.8; margin: 0; font-size: 16px;">For your safety, your account has been temporarily locked due to <strong>multiple failed login attempts</strong>.</p>
                    
                    <div style="background-color: #fff1f2; border-left: 5px solid #e11d48; padding: 32px; border-radius: 18px; margin: 40px 0;">
                        <p style="color: #9f1239; font-size: 18px; margin: 0; font-weight: 800;">
                            Lockout: {lockout_duration} minutes
                        </p>
                    </div>
                    
                    <p style="color: #475569; line-height: 1.8; margin: 0 0 24px; font-size: 16px;">If you forgot your password, you can regain access immediately by using the <a href="{forgot_password_url}" style="color: #ef4444; text-decoration: underline; font-weight: 700;">Forgot Password</a> feature. Otherwise, your account will be automatically unlocked once the lockout period expires.</p>
                    
                    <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; text-align: center; font-weight: 500;">If this wasn't you, we recommend ensuring your email account (e.g., Gmail, Outlook) is secure, as it is the primary way to recover your MyPage48 account.</p>
                </div>
                <div style="background-color: #f1f5f9; padding: 32px; text-align: center;">
                    <p style="color: #0f172a; font-weight: 900; font-size: 14px; margin: 0;">MyPage48</p>
                    <p style="color: #64748b; font-size: 11px; margin: 4px 0 0; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Automated Security System</p>
                </div>
            </div>
        </div>
        """

        payload = {
            "from": self.config.email_from,
            "to": email,
            "subject": "Account Locked - MyPage48",
            "html": html_content,
        }

        if self.background_tasks:
            self.background_tasks.add_task(self._send_email, payload)
        else:
            await self._send_email(payload)

    async def send_feedback_status_update(
        self,
        email: str,
        name: str,
        new_status: str,
        admin_notes: str,
        feedback_message: str,
    ):
        """Send feedback status update notification"""
        feedback_url = f"{self.config.frontend_url}/feedback?tab=my_feedback"

        # Status translations
        status_map = {
            "pending": "Menunggu Review",
            "noted": "Dicatat",
            "in_progress": "Sedang Dikerjakan",
            "implemented": "Telah Diimplementasikan",
            "rejected": "Ditolak",
            "spam": "Spam",
        }

        status_colors = {
            "pending": "#f59e0b",
            "noted": "#3b82f6",
            "in_progress": "#8b5cf6",
            "implemented": "#10b981",
            "rejected": "#ef4444",
            "spam": "#64748b",
        }

        display_status = status_map.get(new_status, new_status)
        status_color = status_colors.get(new_status, "#ef4444")

        notes_html = ""
        if admin_notes:
            escaped_notes = html.escape(admin_notes)
            notes_html = f"""
            <div style="background-color: #f8fafc; padding: 24px; border-radius: 18px; border: 1px dashed #cbd5e1; margin: 30px 0;">
                <p style="color: #64748b; font-size: 11px; margin: 0 0 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;">Catatan dari Admin:</p>
                <p style="color: #334155; font-size: 14px; margin: 0; font-weight: 500; line-height: 1.6;">{escaped_notes}</p>
            </div>
            """

        html_content = f"""
        <div style="background-color: #fdf2f8; padding: 60px 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 28px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.08); border: 1px solid rgba(236, 72, 153, 0.1);">
                <div style="padding: 40px 20px; text-align: center; border-bottom: 1px solid #f1f5f9;">
                    <h1 style="color: #0f172a; margin: 0; font-size: 32px; font-weight: 900; letter-spacing: -0.05em;">MyPage<span style="color: #ef4444;">48</span></h1>
                    <p style="color: #ef4444; margin: 4px 0 0; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 0.2em;">Update Feedback</p>
                </div>
                <div style="padding: 48px 40px;">
                    <h2 style="color: #ef4444; margin: 0 0 16px; font-size: 24px; font-weight: 900; tracking: -0.02em;">Status Laporan Kamu Diperbarui</h2>
                    <p style="color: #475569; line-height: 1.8; margin: 0 0 24px; font-size: 16px;">Halo <strong>{html.escape(name)}</strong>,</p>
                    <p style="color: #475569; line-height: 1.8; margin: 0; font-size: 16px;">Terima kasih telah memberikan masukan untuk MyPage48. Kami ingin mengabarkan bahwa status laporan/saran kamu telah diperbarui.</p>
                    
                    <div style="background-color: #f8fafc; border-left: 5px solid {status_color}; padding: 24px; border-radius: 0 18px 18px 0; margin: 30px 0;">
                        <p style="color: #64748b; font-size: 12px; margin: 0 0 8px; font-weight: 600; text-transform: uppercase;">Masukan Kamu:</p>
                        <p style="color: #475569; font-size: 14px; margin: 0 0 16px; font-style: italic;">"{html.escape(feedback_message)}"</p>
                        
                        <p style="color: #64748b; font-size: 12px; margin: 0 0 8px; font-weight: 600; text-transform: uppercase;">Status Saat Ini:</p>
                        <p style="color: {status_color}; font-size: 18px; margin: 0; font-weight: 800;">{display_status}</p>
                    </div>
                    
                    {notes_html}
                    
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{feedback_url}" 
                           style="background-color: #dc2626; color: #ffffff; padding: 18px 40px; text-decoration: none; border-radius: 18px; display: inline-block; font-weight: 800; font-size: 14px; box-shadow: 0 10px 25px -5px rgba(220, 38, 38, 0.4); transition: all 0.2s ease;">
                            Lihat Semua Feedback Saya
                        </a>
                    </div>
                </div>
                <div style="background-color: #f1f5f9; padding: 32px; text-align: center;">
                    <p style="color: #0f172a; font-weight: 900; font-size: 14px; margin: 0;">MyPage48</p>
                    <p style="color: #64748b; font-size: 11px; margin: 4px 0 0; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Terima kasih atas kontribusimu!</p>
                </div>
            </div>
        </div>
        """

        payload = {
            "from": self.config.email_from,
            "to": email,
            "subject": f"Update Status Masukan: {display_status} - MyPage48",
            "html": html_content,
        }

        if self.background_tasks:
            self.background_tasks.add_task(self._send_email, payload)
        else:
            await self._send_email(payload)
