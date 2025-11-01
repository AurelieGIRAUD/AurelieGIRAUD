"""
Email delivery service using Resend API.

Simple, reliable email delivery following "Boring Pipelines" principle.
"""

import logging
import requests
from typing import Optional


logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """Raised when email delivery fails."""
    pass


class EmailService:
    """
    Email delivery via Resend API.

    Design principle: "Boring Pipelines"
    - Simple HTTP API call (just like Claude)
    - Clear error handling
    - No complex SMTP configuration
    """

    RESEND_API_URL = "https://api.resend.com/emails"

    def __init__(self, api_key: str, from_email: str, to_email: str):
        """
        Initialize email service.

        Args:
            api_key: Resend API key
            from_email: Sender email address
            to_email: Recipient email address
        """
        if not api_key:
            raise ValueError("Resend API key is required")
        if not from_email:
            raise ValueError("From email is required")
        if not to_email:
            raise ValueError("To email is required")

        self.api_key = api_key
        self.from_email = from_email
        self.to_email = to_email

        logger.info(f"Email service initialized: {from_email} → {to_email}")

    def send_report(self, subject: str, html_content: str) -> str:
        """
        Send HTML email report.

        Args:
            subject: Email subject line
            html_content: HTML content for email body

        Returns:
            Email ID from Resend

        Raises:
            EmailDeliveryError: If email delivery fails
        """
        logger.info(f"Sending email: {subject}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "from": self.from_email,
            "to": [self.to_email],
            "subject": subject,
            "html": html_content
        }

        try:
            response = requests.post(
                self.RESEND_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()

            result = response.json()
            email_id = result.get('id', 'unknown')

            logger.info(f"✓ Email sent successfully (ID: {email_id})")
            return email_id

        except requests.exceptions.Timeout:
            raise EmailDeliveryError("Email delivery timed out after 30 seconds")

        except requests.exceptions.RequestException as e:
            error_msg = f"Email delivery failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - Status {e.response.status_code}"

            logger.error(error_msg)
            raise EmailDeliveryError(error_msg)

    def send_test_email(self) -> bool:
        """
        Send a test email to verify configuration.

        Returns:
            True if successful, False otherwise
        """
        try:
            test_html = """
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>🎙️ Podcast Intelligence Test Email</h2>
                <p>This is a test email from your Podcast Intelligence system.</p>
                <p>If you're seeing this, your email configuration is working correctly!</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Sent from Podcast Intelligence CLI
                </p>
            </body>
            </html>
            """

            self.send_report(
                subject="🎙️ Test Email - Podcast Intelligence",
                html_content=test_html
            )

            return True

        except EmailDeliveryError as e:
            logger.error(f"Test email failed: {e}")
            return False
