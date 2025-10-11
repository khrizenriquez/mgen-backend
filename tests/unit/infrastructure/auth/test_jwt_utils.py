"""
Unit tests for JWT utilities
"""
import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from jose import JWTError

from app.infrastructure.auth.jwt_utils import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, verify_token, get_token_expiration,
    create_password_reset_token, verify_password_reset_token,
    create_email_verification_token, verify_email_verification_token
)


@pytest.fixture(autouse=True)
def mock_env():
    """Mock environment variables"""
    with patch.dict(os.environ, {
        'JWT_SECRET_KEY': 'test_secret_key_for_testing_only',
        'ACCESS_TOKEN_EXPIRE_MINUTES': '30',
        'REFRESH_TOKEN_EXPIRE_DAYS': '7'
    }):
        yield


class TestPasswordHashing:
    """Test password hashing and verification"""

    @patch('app.infrastructure.auth.jwt_utils.pwd_context')
    def test_verify_password_success(self, mock_pwd_context):
        """Test successful password verification"""
        mock_pwd_context.verify.return_value = True

        result = verify_password("password123", "hashed_password")

        assert result is True
        mock_pwd_context.verify.assert_called_once_with("password123", "hashed_password")

    @patch('app.infrastructure.auth.jwt_utils.pwd_context')
    def test_verify_password_failure(self, mock_pwd_context):
        """Test failed password verification"""
        mock_pwd_context.verify.return_value = False

        result = verify_password("wrong_password", "hashed_password")

        assert result is False

    @patch('app.infrastructure.auth.jwt_utils.pwd_context')
    def test_get_password_hash(self, mock_pwd_context):
        """Test password hashing"""
        mock_pwd_context.hash.return_value = "hashed_password_123"

        result = get_password_hash("password123")

        assert result == "hashed_password_123"
        mock_pwd_context.hash.assert_called_once_with("password123")


class TestAccessTokenCreation:
    """Test access token creation"""

    @patch('app.infrastructure.auth.jwt_utils.jwt.encode')
    @patch('app.infrastructure.auth.jwt_utils.datetime')
    def test_create_access_token_default_expiry(self, mock_datetime, mock_encode):
        """Test access token creation with default expiry"""
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_encode.return_value = "encoded.jwt.token"

        data = {"sub": "user123", "email": "test@example.com"}
        result = create_access_token(data)

        assert result == "encoded.jwt.token"

        # Check that encode was called with correct data
        call_args = mock_encode.call_args[0]
        encoded_data = call_args[0]
        assert encoded_data["sub"] == "user123"
        assert encoded_data["email"] == "test@example.com"
        assert encoded_data["type"] == "access"
        assert "exp" in encoded_data

    @patch('app.infrastructure.auth.jwt_utils.jwt.encode')
    @patch('app.infrastructure.auth.jwt_utils.datetime')
    def test_create_access_token_custom_expiry(self, mock_datetime, mock_encode):
        """Test access token creation with custom expiry"""
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_encode.return_value = "encoded.jwt.token"

        custom_expiry = timedelta(minutes=60)
        data = {"sub": "user123"}
        result = create_access_token(data, custom_expiry)

        assert result == "encoded.jwt.token"

        # Verify expiry calculation
        expected_expire = datetime(2023, 1, 1, 12, 0, 0) + custom_expiry
        call_args = mock_encode.call_args[0]
        encoded_data = call_args[0]
        assert encoded_data["exp"] == expected_expire


class TestRefreshTokenCreation:
    """Test refresh token creation"""

    @patch('app.infrastructure.auth.jwt_utils.jwt.encode')
    @patch('app.infrastructure.auth.jwt_utils.datetime')
    def test_create_refresh_token(self, mock_datetime, mock_encode):
        """Test refresh token creation"""
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_encode.return_value = "refresh.jwt.token"

        data = {"sub": "user123", "email": "test@example.com"}
        result = create_refresh_token(data)

        assert result == "refresh.jwt.token"

        # Check that encode was called with correct data
        call_args = mock_encode.call_args[0]
        encoded_data = call_args[0]
        assert encoded_data["sub"] == "user123"
        assert encoded_data["email"] == "test@example.com"
        assert encoded_data["type"] == "refresh"
        assert "exp" in encoded_data

        # Check expiry is set to 7 days
        expected_expire = datetime(2023, 1, 1, 12, 0, 0) + timedelta(days=7)
        assert encoded_data["exp"] == expected_expire


class TestTokenVerification:
    """Test token verification"""

    @patch('app.infrastructure.auth.jwt_utils.jwt.decode')
    def test_verify_token_success_access(self, mock_decode):
        """Test successful access token verification"""
        mock_payload = {"sub": "user123", "type": "access", "exp": 1234567890}
        mock_decode.return_value = mock_payload

        result = verify_token("valid.jwt.token", "access")

        assert result == mock_payload
        mock_decode.assert_called_once_with("valid.jwt.token", "test_secret_key_for_testing_only", algorithms=["HS256"])

    @patch('app.infrastructure.auth.jwt_utils.jwt.decode')
    def test_verify_token_success_refresh(self, mock_decode):
        """Test successful refresh token verification"""
        mock_payload = {"sub": "user123", "type": "refresh", "exp": 1234567890}
        mock_decode.return_value = mock_payload

        result = verify_token("valid.refresh.token", "refresh")

        assert result == mock_payload

    @patch('app.infrastructure.auth.jwt_utils.jwt.decode')
    def test_verify_token_type_mismatch(self, mock_decode):
        """Test token type mismatch"""
        mock_payload = {"sub": "user123", "type": "access", "exp": 1234567890}
        mock_decode.return_value = mock_payload

        result = verify_token("access.token", "refresh")

        assert result is None

    @patch('app.infrastructure.auth.jwt_utils.jwt.decode')
    def test_verify_token_decode_error(self, mock_decode):
        """Test token decode error"""
        mock_decode.side_effect = JWTError("Invalid token")

        result = verify_token("invalid.jwt.token")

        assert result is None


class TestTokenExpiration:
    """Test token expiration utilities"""

    @patch('app.infrastructure.auth.jwt_utils.verify_token')
    def test_get_token_expiration_success(self, mock_verify):
        """Test successful token expiration retrieval"""
        mock_payload = {"exp": 1234567890, "sub": "user123"}
        mock_verify.return_value = mock_payload

        result = get_token_expiration("valid.token")

        expected_datetime = datetime.fromtimestamp(1234567890)
        assert result == expected_datetime

    @patch('app.infrastructure.auth.jwt_utils.verify_token')
    def test_get_token_expiration_no_payload(self, mock_verify):
        """Test token expiration with invalid token"""
        mock_verify.return_value = None

        result = get_token_expiration("invalid.token")

        assert result is None

    @patch('app.infrastructure.auth.jwt_utils.verify_token')
    def test_get_token_expiration_no_exp(self, mock_verify):
        """Test token expiration with no exp field"""
        mock_payload = {"sub": "user123"}  # No exp field
        mock_verify.return_value = mock_payload

        result = get_token_expiration("token.without.exp")

        assert result is None


class TestPasswordResetTokens:
    """Test password reset token functionality"""

    @patch('app.infrastructure.auth.jwt_utils.jwt.encode')
    @patch('app.infrastructure.auth.jwt_utils.datetime')
    def test_create_password_reset_token(self, mock_datetime, mock_encode):
        """Test password reset token creation"""
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_encode.return_value = "reset.jwt.token"

        result = create_password_reset_token("test@example.com")

        assert result == "reset.jwt.token"

        # Check encode call
        call_args = mock_encode.call_args[0]
        encoded_data = call_args[0]
        assert encoded_data["sub"] == "test@example.com"
        assert encoded_data["type"] == "password_reset"
        assert "exp" in encoded_data

        # Check expiry is 1 hour
        expected_expire = datetime(2023, 1, 1, 12, 0, 0) + timedelta(hours=1)
        assert encoded_data["exp"] == expected_expire

    @patch('app.infrastructure.auth.jwt_utils.jwt.decode')
    def test_verify_password_reset_token_success(self, mock_decode):
        """Test successful password reset token verification"""
        mock_payload = {"sub": "test@example.com", "type": "password_reset", "exp": 1234567890}
        mock_decode.return_value = mock_payload

        result = verify_password_reset_token("valid.reset.token")

        assert result == "test@example.com"

    @patch('app.infrastructure.auth.jwt_utils.jwt.decode')
    def test_verify_password_reset_token_wrong_type(self, mock_decode):
        """Test password reset token with wrong type"""
        mock_payload = {"sub": "test@example.com", "type": "access", "exp": 1234567890}
        mock_decode.return_value = mock_payload

        result = verify_password_reset_token("wrong.type.token")

        assert result is None

    @patch('app.infrastructure.auth.jwt_utils.jwt.decode')
    def test_verify_password_reset_token_decode_error(self, mock_decode):
        """Test password reset token decode error"""
        mock_decode.side_effect = JWTError("Invalid token")

        result = verify_password_reset_token("invalid.reset.token")

        assert result is None


class TestEmailVerificationTokens:
    """Test email verification token functionality"""

    @patch('app.infrastructure.auth.jwt_utils.jwt.encode')
    @patch('app.infrastructure.auth.jwt_utils.datetime')
    def test_create_email_verification_token(self, mock_datetime, mock_encode):
        """Test email verification token creation"""
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_encode.return_value = "verification.jwt.token"

        user_id = uuid4()
        result = create_email_verification_token(user_id)

        assert result == "verification.jwt.token"

        # Check encode call
        call_args = mock_encode.call_args[0]
        encoded_data = call_args[0]
        assert encoded_data["sub"] == str(user_id)
        assert encoded_data["type"] == "email_verification"
        assert "exp" in encoded_data

        # Check expiry is 1 day
        expected_expire = datetime(2023, 1, 1, 12, 0, 0) + timedelta(days=1)
        assert encoded_data["exp"] == expected_expire

    @patch('app.infrastructure.auth.jwt_utils.jwt.decode')
    def test_verify_email_verification_token_success(self, mock_decode):
        """Test successful email verification token verification"""
        user_id = uuid4()
        mock_payload = {"sub": str(user_id), "type": "email_verification", "exp": 1234567890}
        mock_decode.return_value = mock_payload

        result = verify_email_verification_token("valid.verification.token")

        assert result == user_id

    @patch('app.infrastructure.auth.jwt_utils.jwt.decode')
    def test_verify_email_verification_token_wrong_type(self, mock_decode):
        """Test email verification token with wrong type"""
        user_id = uuid4()
        mock_payload = {"sub": str(user_id), "type": "access", "exp": 1234567890}
        mock_decode.return_value = mock_payload

        result = verify_email_verification_token("wrong.type.token")

        assert result is None

    @patch('app.infrastructure.auth.jwt_utils.jwt.decode')
    def test_verify_email_verification_token_invalid_uuid(self, mock_decode):
        """Test email verification token with invalid UUID"""
        mock_payload = {"sub": "invalid-uuid", "type": "email_verification", "exp": 1234567890}
        mock_decode.return_value = mock_payload

        result = verify_email_verification_token("invalid.uuid.token")

        assert result is None

    @patch('app.infrastructure.auth.jwt_utils.jwt.decode')
    def test_verify_email_verification_token_decode_error(self, mock_decode):
        """Test email verification token decode error"""
        mock_decode.side_effect = JWTError("Invalid token")

        result = verify_email_verification_token("invalid.verification.token")

        assert result is None


class TestJWTUtilsIntegration:
    """Integration tests for JWT utilities"""

    def test_jwt_utils_can_be_imported(self):
        """Test that all JWT utility functions can be imported"""
        from app.infrastructure.auth.jwt_utils import (
            verify_password, get_password_hash, create_access_token,
            create_refresh_token, verify_token, get_token_expiration,
            create_password_reset_token, verify_password_reset_token,
            create_email_verification_token, verify_email_verification_token
        )

        assert callable(verify_password)
        assert callable(get_password_hash)
        assert callable(create_access_token)
        assert callable(create_refresh_token)
        assert callable(verify_token)

    @patch('app.infrastructure.auth.jwt_utils.jwt.encode')
    @patch('app.infrastructure.auth.jwt_utils.jwt.decode')
    def test_token_round_trip(self, mock_decode, mock_encode):
        """Test token creation and verification round trip"""
        mock_encode.return_value = "test.jwt.token"
        mock_decode.return_value = {"sub": "user123", "type": "access", "exp": 1234567890}

        # Create token
        token = create_access_token({"sub": "user123"})

        # Verify token
        payload = verify_token(token, "access")

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_environment_variables_loaded(self):
        """Test that environment variables are properly loaded"""
        from app.infrastructure.auth.jwt_utils import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

        assert SECRET_KEY == "test_secret_key_for_testing_only"
        assert ALGORITHM == "HS256"
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 30