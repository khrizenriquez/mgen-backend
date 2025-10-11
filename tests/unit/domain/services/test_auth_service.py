"""
Unit tests for authentication service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import HTTPException

from app.domain.services.auth_service import AuthService
from app.adapters.schemas.auth_schemas import UserRegister, UserLogin, TokenResponse, UserInfo
from app.infrastructure.database.models import UserModel, RoleModel


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def auth_service(mock_db):
    """Auth service instance with mocked database"""
    return AuthService(mock_db)


@pytest.fixture
def mock_user():
    """Mock user model"""
    user = Mock(spec=UserModel)
    user.id = uuid4()
    user.email = "test@example.com"
    user.password_hash = "hashed_password"
    user.email_verified = False
    user.is_active = True
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    user.user_roles = []
    user.donations = []
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    user = Mock(spec=UserModel)
    user.id = uuid4()
    user.email = "admin@example.com"
    user.user_roles = [Mock(role=Mock(name="ADMIN"))]
    return user


class TestAuthServiceRegisterUser:
    """Test user registration functionality"""

    @patch('app.domain.services.auth_service.validate_email_for_registration')
    @patch('app.domain.services.auth_service.get_password_hash')
    @patch('app.domain.services.auth_service.create_email_verification_token')
    @patch('app.domain.services.auth_service.email_service')
    def test_register_user_success_user_role(self, mock_email_service, mock_token, mock_hash, mock_validate, auth_service, mock_db):
        """Test successful user registration with USER role"""
        mock_validate.return_value = (True, None)
        mock_hash.return_value = "hashed_password"
        mock_token.return_value = "verification_token"
        mock_email_service.send_email_verification_email.return_value = True

        # Mock no existing user
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock role exists
        mock_role = Mock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [None, mock_role]

        user_data = UserRegister(email="test@example.com", password="password123", role="USER")

        result = auth_service.register_user(user_data)

        assert result.email == "test@example.com"
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        mock_email_service.send_email_verification_email.assert_called_once()

    @patch('app.domain.services.auth_service.validate_email_for_registration')
    def test_register_user_invalid_email(self, mock_validate, auth_service):
        """Test registration with invalid email"""
        mock_validate.return_value = (False, "Invalid domain")

        user_data = UserRegister(email="invalid@test.com", password="password123", role="USER")

        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(user_data)

        assert exc_info.value.status_code == 400
        assert "Invalid email" in str(exc_info.value.detail)

    def test_register_user_email_already_exists(self, auth_service, mock_db, mock_user):
        """Test registration when email already exists"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        user_data = UserRegister(email="existing@example.com", password="password123", role="USER")

        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(user_data)

        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)

    def test_register_user_admin_role_without_admin(self, auth_service, mock_db):
        """Test registration with ADMIN role without admin privileges"""
        # Mock no existing user
        mock_db.query.return_value.filter.return_value.first.return_value = None

        user_data = UserRegister(email="test@example.com", password="password123", role="ADMIN")

        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(user_data)

        assert exc_info.value.status_code == 403
        assert "Only administrators can create users with elevated roles" in str(exc_info.value.detail)

    @patch('app.domain.services.auth_service.validate_email_for_registration')
    @patch('app.domain.services.auth_service.get_password_hash')
    def test_register_user_admin_role_with_admin(self, mock_hash, mock_validate, auth_service, mock_db, mock_admin_user):
        """Test registration with ADMIN role by admin user"""
        mock_validate.return_value = (True, None)
        mock_hash.return_value = "hashed_password"

        # Mock no existing user, role exists
        mock_db.query.return_value.filter.return_value.first.side_effect = [None, Mock()]

        user_data = UserRegister(email="test@example.com", password="password123", role="ADMIN")

        result = auth_service.register_user(user_data, mock_admin_user)

        assert result.email == "test@example.com"
        mock_db.add.assert_called()


class TestAuthServiceAuthenticateUser:
    """Test user authentication functionality"""

    @patch('app.domain.services.auth_service.verify_password')
    def test_authenticate_user_success(self, mock_verify, auth_service, mock_db, mock_user):
        """Test successful user authentication"""
        mock_verify.return_value = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        user_data = UserLogin(email="test@example.com", password="password123")

        result = auth_service.authenticate_user(user_data)

        assert result == mock_user

    def test_authenticate_user_not_found(self, auth_service, mock_db):
        """Test authentication when user doesn't exist"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        user_data = UserLogin(email="nonexistent@example.com", password="password123")

        result = auth_service.authenticate_user(user_data)

        assert result is None

    @patch('app.domain.services.auth_service.verify_password')
    def test_authenticate_user_wrong_password(self, mock_verify, auth_service, mock_db, mock_user):
        """Test authentication with wrong password"""
        mock_verify.return_value = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        user_data = UserLogin(email="test@example.com", password="wrongpassword")

        result = auth_service.authenticate_user(user_data)

        assert result is None

    @patch('app.domain.services.auth_service.verify_password')
    def test_authenticate_user_inactive_account(self, mock_verify, auth_service, mock_db, mock_user):
        """Test authentication with inactive account"""
        mock_verify.return_value = True
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        user_data = UserLogin(email="test@example.com", password="password123")

        with pytest.raises(HTTPException) as exc_info:
            auth_service.authenticate_user(user_data)

        assert exc_info.value.status_code == 400
        assert "User account is disabled" in str(exc_info.value.detail)


class TestAuthServiceCreateTokens:
    """Test token creation functionality"""

    @patch('app.domain.services.auth_service.create_access_token')
    @patch('app.domain.services.auth_service.create_refresh_token')
    def test_create_tokens_success(self, mock_refresh_token, mock_access_token, auth_service, mock_user):
        """Test successful token creation"""
        mock_access_token.return_value = "access_token_123"
        mock_refresh_token.return_value = "refresh_token_456"
        mock_user.user_roles = [Mock(role=Mock(name="USER"))]

        result = auth_service.create_tokens(mock_user)

        assert isinstance(result, TokenResponse)
        assert result.access_token == "access_token_123"
        assert result.refresh_token == "refresh_token_456"
        assert result.expires_in == 30 * 60

        mock_access_token.assert_called_once()
        mock_refresh_token.assert_called_once()


class TestAuthServiceRefreshAccessToken:
    """Test token refresh functionality"""

    @patch('app.domain.services.auth_service.verify_token')
    def test_refresh_access_token_success(self, mock_verify, auth_service, mock_db, mock_user):
        """Test successful token refresh"""
        mock_payload = {"sub": str(mock_user.id), "email": mock_user.email}
        mock_verify.return_value = mock_payload
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch.object(auth_service, 'create_tokens') as mock_create_tokens:
            mock_create_tokens.return_value = Mock(spec=TokenResponse)

            result = auth_service.refresh_access_token("valid_refresh_token")

            mock_verify.assert_called_once_with("valid_refresh_token", "refresh")
            mock_create_tokens.assert_called_once_with(mock_user)

    @patch('app.domain.services.auth_service.verify_token')
    def test_refresh_access_token_invalid_token(self, mock_verify, auth_service):
        """Test token refresh with invalid token"""
        mock_verify.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token("invalid_token")

        assert exc_info.value.status_code == 401
        assert "Invalid refresh token" in str(exc_info.value.detail)

    @patch('app.domain.services.auth_service.verify_token')
    def test_refresh_access_token_user_not_found(self, mock_verify, auth_service, mock_db):
        """Test token refresh when user doesn't exist"""
        mock_payload = {"sub": str(uuid4()), "email": "test@example.com"}
        mock_verify.return_value = mock_payload
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token("valid_token")

        assert exc_info.value.status_code == 401
        assert "User not found or inactive" in str(exc_info.value.detail)


class TestAuthServicePasswordReset:
    """Test password reset functionality"""

    @patch('app.domain.services.auth_service.create_password_reset_token')
    @patch('app.domain.services.auth_service.email_service')
    def test_initiate_password_reset_success(self, mock_email_service, mock_token, auth_service, mock_db, mock_user):
        """Test successful password reset initiation"""
        mock_token.return_value = "reset_token_123"
        mock_email_service.send_password_reset_email.return_value = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.initiate_password_reset("test@example.com")

        assert "reset link has been sent" in result
        mock_token.assert_called_once_with("test@example.com")
        mock_email_service.send_password_reset_email.assert_called_once()

    def test_initiate_password_reset_user_not_found(self, auth_service, mock_db):
        """Test password reset initiation for non-existent user"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = auth_service.initiate_password_reset("nonexistent@example.com")

        assert "reset link has been sent" in result

    @patch('app.domain.services.auth_service.verify_password_reset_token')
    @patch('app.domain.services.auth_service.get_password_hash')
    def test_reset_password_success(self, mock_hash, mock_verify, auth_service, mock_db, mock_user):
        """Test successful password reset"""
        mock_verify.return_value = "test@example.com"
        mock_hash.return_value = "new_hashed_password"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.reset_password("valid_token", "newpassword123")

        assert "Password reset successfully" in result
        assert mock_user.password_hash == "new_hashed_password"
        mock_db.commit.assert_called_once()

    @patch('app.domain.services.auth_service.verify_password_reset_token')
    def test_reset_password_invalid_token(self, mock_verify, auth_service):
        """Test password reset with invalid token"""
        mock_verify.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            auth_service.reset_password("invalid_token", "newpassword123")

        assert exc_info.value.status_code == 400
        assert "Invalid or expired reset token" in str(exc_info.value.detail)


class TestAuthServiceEmailVerification:
    """Test email verification functionality"""

    @patch('app.domain.services.auth_service.verify_email_verification_token')
    def test_verify_email_success(self, mock_verify, auth_service, mock_db, mock_user):
        """Test successful email verification"""
        mock_verify.return_value = mock_user.id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch('app.domain.services.auth_service.email_service') as mock_email_service:
            mock_email_service.send_welcome_email.return_value = True

            result = auth_service.verify_email("valid_token")

            assert "Email verified successfully" in result
            assert mock_user.email_verified is True
            mock_db.commit.assert_called_once()

    @patch('app.domain.services.auth_service.verify_email_verification_token')
    def test_verify_email_invalid_token(self, mock_verify, auth_service):
        """Test email verification with invalid token"""
        mock_verify.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_email("invalid_token")

        assert exc_info.value.status_code == 400
        assert "Invalid or expired verification token" in str(exc_info.value.detail)

    @patch('app.domain.services.auth_service.verify_email_verification_token')
    def test_verify_email_already_verified(self, mock_verify, auth_service, mock_db, mock_user):
        """Test email verification when already verified"""
        mock_verify.return_value = mock_user.id
        mock_user.email_verified = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.verify_email("valid_token")

        assert "Email already verified" in result
        assert mock_user.email_verified is True


class TestAuthServiceChangePassword:
    """Test password change functionality"""

    @patch('app.domain.services.auth_service.verify_password')
    @patch('app.domain.services.auth_service.get_password_hash')
    def test_change_password_success(self, mock_hash, mock_verify, auth_service, mock_db, mock_user):
        """Test successful password change"""
        mock_verify.return_value = True
        mock_hash.return_value = "new_hashed_password"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.change_password(mock_user.id, "current_password", "new_password")

        assert "Password changed successfully" in result
        assert mock_user.password_hash == "new_hashed_password"
        mock_db.commit.assert_called_once()

    @patch('app.domain.services.auth_service.verify_password')
    def test_change_password_wrong_current_password(self, mock_verify, auth_service, mock_db, mock_user):
        """Test password change with wrong current password"""
        mock_verify.return_value = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(HTTPException) as exc_info:
            auth_service.change_password(mock_user.id, "wrong_password", "new_password")

        assert exc_info.value.status_code == 400
        assert "Current password is incorrect" in str(exc_info.value.detail)

    def test_change_password_user_not_found(self, auth_service, mock_db):
        """Test password change for non-existent user"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            auth_service.change_password(uuid4(), "current_password", "new_password")

        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)


class TestAuthServiceDashboard:
    """Test dashboard functionality"""

    def test_get_dashboard_data_success(self, auth_service, mock_user):
        """Test successful dashboard data retrieval"""
        mock_user.user_roles = [Mock(role=Mock(name="USER"))]

        with patch.object(auth_service, '_get_role_based_stats') as mock_stats, \
             patch.object(auth_service, '_get_recent_activity') as mock_activity:

            mock_stats.return_value = {"account_status": "Active"}
            mock_activity.return_value = []

            result = auth_service.get_dashboard_data(mock_user)

            assert result.user.email == mock_user.email
            assert result.stats == {"account_status": "Active"}
            assert result.recent_activity == []

    def test_get_role_based_stats_admin(self, auth_service, mock_user):
        """Test role-based stats for admin user"""
        roles = ["ADMIN"]
        mock_user.user_roles = [Mock(role=Mock(name="ADMIN"))]

        # Mock database queries
        auth_service.db.query.return_value.count.return_value = 10

        stats = auth_service._get_role_based_stats(mock_user, roles)

        assert "total_users" in stats
        assert "system_health" in stats

    def test_get_role_based_stats_donor(self, auth_service, mock_user):
        """Test role-based stats for donor user"""
        roles = ["DONOR"]
        mock_donation = Mock()
        mock_donation.amount_gtq = 100.0
        mock_donation.status_id = 2
        mock_user.donations = [mock_donation]

        stats = auth_service._get_role_based_stats(mock_user, roles)

        assert stats["my_donations"] == 1
        assert stats["total_donated_gtq"] == 100.0

    def test_get_recent_activity_donor(self, auth_service, mock_user):
        """Test recent activity for donor user"""
        roles = ["DONOR"]
        mock_donation = Mock()
        mock_donation.amount_gtq = 50.0
        mock_donation.created_at = datetime.utcnow()
        mock_donation.status_id = 2
        mock_user.donations = [mock_donation]

        activity = auth_service._get_recent_activity(mock_user, roles)

        assert len(activity) >= 1
        assert activity[0]["type"] == "donation"
        assert "Q50.0" in activity[0]["description"]


class TestAuthServiceRoleChange:
    """Test role change functionality"""

    def test_change_user_role_to_donor_success(self, auth_service, mock_db, mock_user):
        """Test successful role change to donor"""
        mock_user.user_roles = [Mock(role=Mock(name="USER"))]
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, Mock()]  # user, donor_role

        result = auth_service.change_user_role_to_donor(mock_user.id)

        assert "Successfully upgraded to donor status" in result
        mock_db.delete.assert_called_once()  # Remove USER role
        mock_db.add.assert_called()  # Add DONOR role
        mock_db.commit.assert_called_once()

    def test_change_user_role_to_donor_already_donor(self, auth_service, mock_db, mock_user):
        """Test role change when user is already donor"""
        mock_user.user_roles = [Mock(role=Mock(name="DONOR"))]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.change_user_role_to_donor(mock_user.id)

        assert "User is already a donor" in result
        mock_db.delete.assert_not_called()
        mock_db.add.assert_not_called()

    def test_change_user_role_to_donor_not_user(self, auth_service, mock_db, mock_user):
        """Test role change when user is not a regular user"""
        mock_user.user_roles = [Mock(role=Mock(name="ADMIN"))]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(HTTPException) as exc_info:
            auth_service.change_user_role_to_donor(mock_user.id)

        assert exc_info.value.status_code == 400
        assert "Only regular users can upgrade to donor status" in str(exc_info.value.detail)


class TestAuthServiceAdminFunctions:
    """Test admin-only functionality"""

    def test_get_all_users_success(self, auth_service, mock_db, mock_user):
        """Test successful retrieval of all users"""
        mock_user.user_roles = [Mock(role=Mock(name="USER"))]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_user]

        result = auth_service.get_all_users()

        assert len(result) == 1
        assert isinstance(result[0], UserInfo)
        assert result[0].email == mock_user.email

    def test_logout_user_success(self, auth_service, mock_user):
        """Test successful user logout"""
        result = auth_service.logout_user(mock_user)

        assert "Logged out successfully" in result


class TestAuthServiceIntegration:
    """Integration tests for auth service"""

    def test_auth_service_initialization(self, mock_db):
        """Test auth service can be initialized"""
        service = AuthService(mock_db)
        assert service.db == mock_db

    def test_register_user_creates_user_with_correct_data(self, auth_service, mock_db):
        """Test that register_user creates user with all required data"""
        with patch('app.domain.services.auth_service.validate_email_for_registration') as mock_validate, \
             patch('app.domain.services.auth_service.get_password_hash') as mock_hash, \
             patch('app.domain.services.auth_service.create_email_verification_token') as mock_token, \
             patch('app.domain.services.auth_service.email_service') as mock_email:

            mock_validate.return_value = (True, None)
            mock_hash.return_value = "hashed_pass"
            mock_token.return_value = "token"
            mock_email.send_email_verification_email.return_value = True

            # Mock database queries
            mock_db.query.return_value.filter.return_value.first.side_effect = [None, Mock()]  # No user, role exists

            user_data = UserRegister(email="newuser@test.com", password="pass123", role="USER")

            result = auth_service.register_user(user_data)

            # Verify user was created with correct data
            assert result.email == "newuser@test.com"
            assert hasattr(result, 'password_hash')
            assert result.email_verified == False
            assert result.is_active == True