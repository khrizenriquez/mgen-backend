"""
Email service for sending notifications and password resets
"""
import os
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Service for sending emails via SendGrid API"""

    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@donacionesgt.org")
        self.from_name = os.getenv("FROM_NAME", "Sistema de Donaciones")

        if self.api_key:
            self.sendgrid = SendGridAPIClient(api_key=self.api_key)
        else:
            self.sendgrid = None
            logger.warning("SendGrid API key not configured")

        # Validate FRONTEND_URL for email functionality that requires it
        self.frontend_url = os.getenv('FRONTEND_URL')
        if not self.frontend_url:
            logger.warning("FRONTEND_URL environment variable not set - password reset and email verification will fail")

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)

        Returns:
            bool: True if email was sent successfully
        """
        try:
            if not self.sendgrid:
                logger.error("SendGrid client not initialized - check API key")
                return False

            # Create email message
            from_email = Email(email=self.from_email, name=self.from_name)
            to_email_obj = To(to_email)

            mail = Mail(from_email, to_email_obj, subject, Content("text/html", html_content))

            # Add text content if provided
            if text_content:
                mail.add_content(Content("text/plain", text_content))

            # Send email
            response = self.sendgrid.send(mail)

            if response.status_code in [200, 201, 202]:
                logger.info("Email sent successfully to: {to_email}")
                return True
            else:
                logger.error(
                    "SendGrid reported failure for {to_email}: {response.status_code} - {response.body}",
                    to_email=to_email,
                    status_code=response.status_code,
                    response_body=response.body.decode('utf-8') if hasattr(response, 'body') else str(response)
                )
                return False

        except Exception as e:
            logger.error("Failed to send email to {to_email}: {error}", to_email=to_email, error=str(e), exc_info=True)
            return False

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        if not self.frontend_url:
            logger.error("FRONTEND_URL environment variable not set")
            return False
        reset_url = f"{self.frontend_url}/reset-password?token={reset_token}"

        subject = "Password Reset Request"
        html_content = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested a password reset for your account.</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this reset, please ignore this email.</p>
            <br>
            <p>Best regards,<br>Donations Management System</p>
        </body>
        </html>
        """

        text_content = f"""
        Password Reset Request

        You requested a password reset for your account.

        Reset your password here: {reset_url}

        This link will expire in 1 hour.

        If you didn't request this reset, please ignore this email.

        Best regards,
        Donations Management System
        """

        return self.send_email(to_email, subject, html_content, text_content)

    def send_email_verification_email(self, to_email: str, verification_token: str) -> bool:
        """Send email verification email"""
        if not self.frontend_url:
            logger.error("FRONTEND_URL environment variable not set")
            return False
        verification_url = f"{self.frontend_url}/verify-email?token={verification_token}"

        subject = "Verify Your Email Address"
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to Donations Management System</h2>
            <p>Please verify your email address to complete your registration.</p>
            <p>Click the link below to verify your email:</p>
            <p><a href="{verification_url}">Verify Email</a></p>
            <p>This link will expire in 24 hours.</p>
            <br>
            <p>Best regards,<br>Donations Management System</p>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to Donations Management System

        Please verify your email address to complete your registration.

        Verify your email here: {verification_url}

        This link will expire in 24 hours.

        Best regards,
        Donations Management System
        """

        return self.send_email(to_email, subject, html_content, text_content)

    def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Send welcome email after successful registration and verification"""
        subject = "Welcome to Donations Management System"
        html_content = f"""
        <html>
        <body>
            <h2>Welcome, {user_name}!</h2>
            <p>Your account has been successfully verified.</p>
            <p>You can now log in and start using the Donations Management System.</p>
            <br>
            <p>Best regards,<br>Donations Management System Team</p>
        </body>
        </html>
        """

        text_content = f"""
        Welcome, {user_name}!

        Your account has been successfully verified.

        You can now log in and start using the Donations Management System.

        Best regards,
        Donations Management System Team
        """

        return self.send_email(to_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()