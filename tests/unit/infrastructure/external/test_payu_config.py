"""
Tests for PayU configuration
"""
import os
import pytest
from unittest.mock import patch

from app.infrastructure.external.payu_config import PayUConfig


class TestPayUConfig:
    """Test PayU configuration class"""

    @patch.dict(os.environ, {
        "PAYU_API_KEY": "test_api_key",
        "PAYU_API_LOGIN": "test_api_login",
        "PAYU_MERCHANT_ID": "test_merchant_id",
        "PAYU_PUBLIC_KEY": "test_public_key",
        "PAYU_TEST_MODE": "true",
        "PAYU_COUNTRY_CODE": "GT",
        "PAYU_CURRENCY": "GTQ"
    })
    def test_config_with_valid_env_vars(self):
        """Test configuration with valid environment variables"""
        config = PayUConfig()

        assert config.API_KEY == "test_api_key"
        assert config.API_LOGIN == "test_api_login"
        assert config.MERCHANT_ID == "test_merchant_id"
        assert config.PUBLIC_KEY == "test_public_key"
        assert config.TEST_MODE is True
        assert config.COUNTRY_CODE == "GT"
        assert config.CURRENCY == "GTQ"

    def test_config_with_default_test_credentials(self):
        """Test configuration with default test credentials"""
        config = PayUConfig()

        # Should use the test credentials provided by user
        assert config.API_KEY == "4Vj8eK4rloUd272L48hsrarnUA"
        assert config.API_LOGIN == "pRRXKOl8ikMmt9u"
        assert config.MERCHANT_ID == "508029"
        assert config.PUBLIC_KEY == "PKaC6H4cEDJD919n705L544kSU"

    def test_get_account_id_by_country(self):
        """Test getting account ID for different countries"""
        config = PayUConfig()

        assert config.get_account_id("GT") == "512322"  # Guatemala
        assert config.get_account_id("AR") == "512322"  # Argentina
        assert config.get_account_id("BR") == "512327"  # Brazil
        assert config.get_account_id("CO") == "512321"  # Colombia
        assert config.get_account_id("MX") == "512324"  # Mexico
        assert config.get_account_id("XX") == "512322"  # Unknown defaults to GT

    def test_api_urls(self):
        """Test API URL generation"""
        config = PayUConfig()

        assert config.get_api_url("") == "https://sandbox.api.payulatam.com/payments-api/4.0/service.cgi"
        assert config.get_reports_url("") == "https://sandbox.api.payulatam.com/reports-api/4.0/service.cgi"

        # Test production URLs
        config.TEST_MODE = False
        assert "api.payulatam.com" in config.BASE_URL

    def test_validate_config_success(self):
        """Test configuration validation with all required fields"""
        config = PayUConfig()
        errors = config.validate_config()

        # With default test credentials, should have no errors
        assert len(errors) == 0

    @patch.dict(os.environ, {
        "PAYU_API_KEY": "",
        "PAYU_API_LOGIN": "",
        "PAYU_MERCHANT_ID": "",
        "PAYU_PUBLIC_KEY": ""
    }, clear=True)
    def test_validate_config_missing_fields(self):
        """Test configuration validation with missing fields"""
        config = PayUConfig()
        errors = config.validate_config()

        assert len(errors) > 0
        assert any("PAYU_API_KEY" in error for error in errors)
        assert any("PAYU_API_LOGIN" in error for error in errors)
        assert any("PAYU_MERCHANT_ID" in error for error in errors)
        assert any("PAYU_PUBLIC_KEY" in error for error in errors)

    def test_is_production(self):
        """Test production mode detection"""
        config = PayUConfig()

        config.TEST_MODE = False
        assert config.is_production() is True

        config.TEST_MODE = True
        assert config.is_production() is False
