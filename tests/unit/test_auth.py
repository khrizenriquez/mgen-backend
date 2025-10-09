"""
Unit tests for authentication system
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
import os

from app.infrastructure.auth.jwt_utils import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, verify_token, SECRET_KEY
)
from app.domain.services.auth_service import AuthService
from app.adapters.schemas.auth_schemas import UserRegister, UserLogin


class TestJWTUtils:
    """Test JWT utilities"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        test_data = {"sub": "test@example.com", "roles": ["USER"]}

        # Test access token
        access_token = create_access_token(test_data)
        payload = verify_token(access_token, "access")

        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["roles"] == ["USER"]
        assert payload["type"] == "access"

        # Test refresh token
        refresh_token = create_refresh_token(test_data)
        refresh_payload = verify_token(refresh_token, "refresh")

        assert refresh_payload is not None
        assert refresh_payload["type"] == "refresh"

    def test_invalid_token_verification(self):
        """Test invalid token handling"""
        assert verify_token("invalid.token.here", "access") is None
        assert verify_token("", "access") is None


class TestAuthService:
    """Test authentication service"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def auth_service(self, mock_db):
        """Auth service instance"""
        return AuthService(mock_db)

    def test_register_user_success(self, auth_service, mock_db):
        """Test successful user registration"""
        # Mock existing user check
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock role lookup
        mock_role = Mock()
        mock_role.name = "USER"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_role

        # Mock user creation
        mock_user = Mock()
        mock_user.id = "test-uuid"
        mock_user.email = "test@example.com"
        mock_db.add.return_value = None
        mock_db.flush.return_value = None
        mock_db.refresh.return_value = None

        user_data = UserRegister(
            email="test@example.com",
            password="password123",
            role="USER"
        )

        with patch('app.infrastructure.external.email_service.email_service.send_email_verification_email') as mock_email:
            mock_email.return_value = True
            result = auth_service.register_user(user_data)

            assert result is not None
            mock_email.assert_called_once()

    def test_register_duplicate_email(self, auth_service, mock_db):
        """Test registration with duplicate email"""
        # Mock existing user
        mock_existing_user = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_user

        user_data = UserRegister(
            email="existing@example.com",
            password="password123",
            role="USER"
        )

        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(user_data)

        assert exc_info.value.status_code == 400
        assert "already registered" in str(exc_info.value.detail)

    def test_authenticate_user_success(self, auth_service, mock_db):
        """Test successful user authentication"""
        user_data = UserLogin(email="test@example.com", password="password123")

        # Mock user lookup
        mock_user = Mock()
        mock_user.password_hash = get_password_hash("password123")
        mock_user.is_active = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.authenticate_user(user_data)
        assert result == mock_user

    def test_authenticate_user_wrong_password(self, auth_service, mock_db):
        """Test authentication with wrong password"""
        user_data = UserLogin(email="test@example.com", password="wrongpassword")

        # Mock user lookup
        mock_user = Mock()
        mock_user.password_hash = get_password_hash("correctpassword")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.authenticate_user(user_data)
        assert result is None

    def test_authenticate_inactive_user(self, auth_service, mock_db):
        """Test authentication of inactive user"""
        user_data = UserLogin(email="test@example.com", password="password123")

        # Mock inactive user
        mock_user = Mock()
        mock_user.password_hash = get_password_hash("password123")
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(HTTPException) as exc_info:
            auth_service.authenticate_user(user_data)

        assert exc_info.value.status_code == 400
        assert "disabled" in str(exc_info.value.detail)

    def test_logout_user(self, auth_service, mock_db):
        """Test user logout"""
        # Mock user
        mock_user = Mock()
        mock_user.email = "test@example.com"

        result = auth_service.logout_user(mock_user)
        assert result == "Logged out successfully"


class TestSecurityValidation:
    """Test security validations"""

    def test_jwt_secret_required(self):
        """Test that JWT_SECRET_KEY is required"""
        # Remove env var if exists
        original_value = os.environ.get('JWT_SECRET_KEY')
        if 'JWT_SECRET_KEY' in os.environ:
            del os.environ['JWT_SECRET_KEY']

        try:
            # This should fail
            with pytest.raises(ValueError, match="JWT_SECRET_KEY environment variable is required"):
                # Force re-evaluation of the module
                import importlib
                import app.infrastructure.auth.jwt_utils
                importlib.reload(app.infrastructure.auth.jwt_utils)
                _ = app.infrastructure.auth.jwt_utils.SECRET_KEY
        finally:
            # Restore original value
            if original_value:
                os.environ['JWT_SECRET_KEY'] = original_value