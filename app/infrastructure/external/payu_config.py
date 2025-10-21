"""
PayU Configuration - Payment gateway settings and credentials
"""
import os
from typing import Optional


class PayUConfig:
    """Configuration class for PayU payment gateway"""

    # API Credentials
    API_KEY: str = os.getenv("PAYU_API_KEY", "4Vj8eK4rloUd272L48hsrarnUA")
    API_LOGIN: str = os.getenv("PAYU_API_LOGIN", "pRRXKOl8ikMmt9u")
    MERCHANT_ID: str = os.getenv("PAYU_MERCHANT_ID", "508029")
    PUBLIC_KEY: str = os.getenv("PAYU_PUBLIC_KEY", "PKaC6H4cEDJD919n705L544kSU")

    # Account IDs by country
    ACCOUNT_IDS = {
        "AR": os.getenv("PAYU_ACCOUNT_ID_AR", "512322"),  # Argentina
        "BR": os.getenv("PAYU_ACCOUNT_ID_BR", "512327"),  # Brazil
        "CL": os.getenv("PAYU_ACCOUNT_ID_CL", "512325"),  # Chile
        "CO": os.getenv("PAYU_ACCOUNT_ID_CO", "512321"),  # Colombia
        "MX": os.getenv("PAYU_ACCOUNT_ID_MX", "512324"),  # Mexico
        "PA": os.getenv("PAYU_ACCOUNT_ID_PA", "512326"),  # Panama
        "PE": os.getenv("PAYU_ACCOUNT_ID_PE", "512323"),  # Peru
        "GT": os.getenv("PAYU_ACCOUNT_ID_GT", "512322"),  # Guatemala
    }

    # Environment settings
    TEST_MODE: bool = os.getenv("PAYU_TEST_MODE", "true").lower() == "true"
    COUNTRY_CODE: str = os.getenv("PAYU_COUNTRY_CODE", "GT")
    CURRENCY: str = os.getenv("PAYU_CURRENCY", "GTQ")

    # API URLs
    BASE_URL: str = os.getenv(
        "PAYU_BASE_URL",
        "https://sandbox.api.payulatam.com" if TEST_MODE else "https://api.payulatam.com"
    )

    PAYMENTS_URL: str = os.getenv(
        "PAYU_PAYMENTS_URL",
        "https://sandbox.checkout.payulatam.com/ppp-web-gateway-payu" if TEST_MODE
        else "https://checkout.payulatam.com/ppp-web-gateway-payu"
    )

    # Webhook configuration
    WEBHOOK_SECRET: Optional[str] = os.getenv("PAYU_WEBHOOK_SECRET")
    WEBHOOK_URL: str = os.getenv("PAYU_WEBHOOK_URL", "")

    # Timeouts and retry configuration
    REQUEST_TIMEOUT: int = int(os.getenv("PAYU_REQUEST_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("PAYU_MAX_RETRIES", "3"))
    RETRY_DELAY: int = int(os.getenv("PAYU_RETRY_DELAY", "5"))

    @classmethod
    def get_account_id(cls, country_code: str = None) -> str:
        """Get account ID for specific country"""
        country = country_code or cls.COUNTRY_CODE
        return cls.ACCOUNT_IDS.get(country.upper(), cls.ACCOUNT_IDS["GT"])

    @classmethod
    def get_api_url(cls, endpoint: str) -> str:
        """Get full API URL for endpoint"""
        return f"{cls.BASE_URL}/payments-api/4.0/service.cgi"

    @classmethod
    def get_reports_url(cls, endpoint: str) -> str:
        """Get full reports API URL for endpoint"""
        return f"{cls.BASE_URL}/reports-api/4.0/service.cgi"

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production mode"""
        return not cls.TEST_MODE

    @classmethod
    def validate_config(cls) -> list[str]:
        """Validate PayU configuration and return list of missing/invalid settings"""
        errors = []

        required_fields = [
            ("API_KEY", cls.API_KEY),
            ("API_LOGIN", cls.API_LOGIN),
            ("MERCHANT_ID", cls.MERCHANT_ID),
            ("PUBLIC_KEY", cls.PUBLIC_KEY),
        ]

        for field_name, value in required_fields:
            if not value or value == f"your-{field_name.lower()}-here":
                errors.append(f"PAYU_{field_name} is not configured")

        if cls.COUNTRY_CODE not in cls.ACCOUNT_IDS:
            errors.append(f"Unsupported country code: {cls.COUNTRY_CODE}")

        return errors


# Convenience instance
payu_config = PayUConfig()
