"""
Email service for sending notifications and password resets
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Service for sending emails"""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

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
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            # Add text content
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))

            # Add HTML content
            msg.attach(MIMEText(html_content, 'html'))

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()

            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            server.sendmail(self.from_email, to_email, msg.as_string())
            server.quit()

            logger.info(f"Email sent successfully to: {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return False

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"

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
        verification_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={verification_token}"

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