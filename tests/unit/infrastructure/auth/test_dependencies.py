"""
Unit tests for authentication dependencies
"""
import pytest
from unittest.mock import Mock, patch
from uuid import UUID, uuid4
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.infrastructure.auth.dependencies import (
    get_current_user, get_current_active_user, get_user_roles,
    require_admin, require_organization, require_auditor,
    require_role, require_any_role, get_optional_current_user,
    user_to_user_info
)
from app.adapters.schemas.auth_schemas import UserInfo


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def mock_user():
    """Mock user model"""
    user = Mock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.email_verified = False
    user.is_active = True
    user.created_at = "2023-01-01T00:00:00"
    user.updated_at = "2023-01-01T00:00:00"
    user.user_roles = []
    return user


@pytest.fixture
def mock_credentials():
    """Mock HTTP authorization credentials"""
    return Mock(spec=HTTPAuthorizationCredentials, credentials="valid.jwt.token")


class TestGetCurrentUser:
    """Test get_current_user dependency"""

    @patch('app.infrastructure.auth.dependencies.verify_token')
    def test_get_current_user_success(self, mock_verify, mock_db, mock_user, mock_credentials):
        """Test successful user retrieval"""
        mock_payload = {"sub": str(mock_user.id), "email": mock_user.email}
        mock_verify.return_value = mock_payload
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = get_current_user(mock_credentials, mock_db)

        assert result == mock_user
        mock_verify.assert_called_once_with("valid.jwt.token", "access")

    @patch('app.infrastructure.auth.dependencies.verify_token')
    def test_get_current_user_invalid_token(self, mock_verify, mock_db, mock_credentials):
        """Test invalid token handling"""
        mock_verify.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, mock_db)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @patch('app.infrastructure.auth.dependencies.verify_token')
    def test_get_current_user_no_user_id(self, mock_verify, mock_db, mock_credentials):
        """Test token without user ID"""
        mock_payload = {"email": "test@example.com"}  # No 'sub' field
        mock_verify.return_value = mock_payload

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, mock_db)

        assert exc_info.value.status_code == 401

    @patch('app.infrastructure.auth.dependencies.verify_token')
    def test_get_current_user_invalid_uuid(self, mock_verify, mock_db, mock_credentials):
        """Test invalid UUID in token"""
        mock_payload = {"sub": "invalid-uuid", "email": "test@example.com"}
        mock_verify.return_value = mock_payload

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, mock_db)

        assert exc_info.value.status_code == 401

    @patch('app.infrastructure.auth.dependencies.verify_token')
    def test_get_current_user_not_found(self, mock_verify, mock_db, mock_credentials):
        """Test user not found in database"""
        mock_payload = {"sub": str(uuid4()), "email": "test@example.com"}
        mock_verify.return_value = mock_payload
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, mock_db)

        assert exc_info.value.status_code == 401

    @patch('app.infrastructure.auth.dependencies.verify_token')
    def test_get_current_user_inactive(self, mock_verify, mock_db, mock_user, mock_credentials):
        """Test inactive user handling"""
        mock_payload = {"sub": str(mock_user.id), "email": mock_user.email}
        mock_verify.return_value = mock_payload
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, mock_db)

        assert exc_info.value.status_code == 400
        assert "Inactive user" in str(exc_info.value.detail)


class TestGetCurrentActiveUser:
    """Test get_current_active_user dependency"""

    def test_get_current_active_user_alias(self, mock_user):
        """Test that get_current_active_user is alias for get_current_user"""
        # This function just returns the current_user parameter
        result = get_current_active_user(mock_user)
        assert result == mock_user


class TestGetUserRoles:
    """Test get_user_roles function"""

    def test_get_user_roles_success(self, mock_user):
        """Test successful role extraction"""
        mock_role1 = Mock()
        mock_role1.role.name = "ADMIN"
        mock_role2 = Mock()
        mock_role2.role.name = "USER"
        mock_user.user_roles = [mock_role1, mock_role2]

        result = get_user_roles(mock_user)

        assert result == ["ADMIN", "USER"]

    def test_get_user_roles_empty(self, mock_user):
        """Test user with no roles"""
        mock_user.user_roles = []

        result = get_user_roles(mock_user)

        assert result == []


class TestRequireAdmin:
    """Test require_admin dependency"""

    def test_require_admin_success(self, mock_user):
        """Test admin role requirement success"""
        mock_role = Mock()
        mock_role.role.name = "ADMIN"
        mock_user.user_roles = [mock_role]

        result = require_admin(mock_user)

        assert result == mock_user

    def test_require_admin_failure(self, mock_user):
        """Test admin role requirement failure"""
        mock_role = Mock()
        mock_role.role.name = "USER"
        mock_user.user_roles = [mock_role]

        with pytest.raises(HTTPException) as exc_info:
            require_admin(mock_user)

        assert exc_info.value.status_code == 403
        assert "Admin role required" in str(exc_info.value.detail)


class TestRequireOrganization:
    """Test require_organization dependency"""

    def test_require_organization_admin_success(self, mock_user):
        """Test organization requirement with admin role"""
        mock_role = Mock()
        mock_role.role.name = "ADMIN"
        mock_user.user_roles = [mock_role]

        result = require_organization(mock_user)

        assert result == mock_user

    def test_require_organization_org_success(self, mock_user):
        """Test organization requirement with organization role"""
        mock_role = Mock()
        mock_role.role.name = "ORGANIZATION"
        mock_user.user_roles = [mock_role]

        result = require_organization(mock_user)

        assert result == mock_user

    def test_require_organization_failure(self, mock_user):
        """Test organization requirement failure"""
        mock_role = Mock()
        mock_role.role.name = "USER"
        mock_user.user_roles = [mock_role]

        with pytest.raises(HTTPException) as exc_info:
            require_organization(mock_user)

        assert exc_info.value.status_code == 403
        assert "Organization or Admin role required" in str(exc_info.value.detail)


class TestRequireAuditor:
    """Test require_auditor dependency"""

    def test_require_auditor_admin_success(self, mock_user):
        """Test auditor requirement with admin role"""
        mock_role = Mock()
        mock_role.role.name = "ADMIN"
        mock_user.user_roles = [mock_role]

        result = require_auditor(mock_user)

        assert result == mock_user

    def test_require_auditor_auditor_success(self, mock_user):
        """Test auditor requirement with auditor role"""
        mock_role = Mock()
        mock_role.role.name = "AUDITOR"
        mock_user.user_roles = [mock_role]

        result = require_auditor(mock_user)

        assert result == mock_user

    def test_require_auditor_failure(self, mock_user):
        """Test auditor requirement failure"""
        mock_role = Mock()
        mock_role.role.name = "USER"
        mock_user.user_roles = [mock_role]

        with pytest.raises(HTTPException) as exc_info:
            require_auditor(mock_user)

        assert exc_info.value.status_code == 403
        assert "Auditor, Organization or Admin role required" in str(exc_info.value.detail)


class TestRequireRole:
    """Test require_role dependency factory"""

    def test_require_role_success(self, mock_user):
        """Test specific role requirement success"""
        mock_role = Mock()
        mock_role.role.name = "DONOR"
        mock_user.user_roles = [mock_role]

        role_checker = require_role("DONOR")
        result = role_checker(mock_user, ["DONOR"])

        assert result == mock_user

    def test_require_role_failure(self, mock_user):
        """Test specific role requirement failure"""
        mock_role = Mock()
        mock_role.role.name = "USER"
        mock_user.user_roles = [mock_role]

        role_checker = require_role("DONOR")

        with pytest.raises(HTTPException) as exc_info:
            role_checker(mock_user, ["USER"])

        assert exc_info.value.status_code == 403
        assert "Role 'DONOR' required" in str(exc_info.value.detail)


class TestRequireAnyRole:
    """Test require_any_role dependency factory"""

    def test_require_any_role_success(self, mock_user):
        """Test any role requirement success"""
        mock_role = Mock()
        mock_role.role.name = "DONOR"
        mock_user.user_roles = [mock_role]

        role_checker = require_any_role("DONOR", "ADMIN")
        result = role_checker(mock_user, ["DONOR"])

        assert result == mock_user

    def test_require_any_role_failure(self, mock_user):
        """Test any role requirement failure"""
        mock_role = Mock()
        mock_role.role.name = "USER"
        mock_user.user_roles = [mock_role]

        role_checker = require_any_role("DONOR", "ADMIN")

        with pytest.raises(HTTPException) as exc_info:
            role_checker(mock_user, ["USER"])

        assert exc_info.value.status_code == 403
        assert "One of roles" in str(exc_info.value.detail)


class TestGetOptionalCurrentUser:
    """Test get_optional_current_user dependency"""

    @patch('app.infrastructure.auth.dependencies.verify_token')
    def test_get_optional_current_user_no_credentials(self, mock_verify, mock_db):
        """Test optional user with no credentials"""
        result = get_optional_current_user(None, mock_db)

        assert result is None
        mock_verify.assert_not_called()

    @patch('app.infrastructure.auth.dependencies.verify_token')
    def test_get_optional_current_user_success(self, mock_verify, mock_db, mock_user):
        """Test optional user retrieval success"""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials, credentials="valid.jwt.token")
        mock_payload = {"sub": str(mock_user.id), "email": mock_user.email}
        mock_verify.return_value = mock_payload
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = get_optional_current_user(mock_credentials, mock_db)

        assert result == mock_user

    @patch('app.infrastructure.auth.dependencies.verify_token')
    def test_get_optional_current_user_invalid_token(self, mock_verify, mock_db):
        """Test optional user with invalid token"""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials, credentials="invalid.jwt.token")
        mock_verify.return_value = None

        result = get_optional_current_user(mock_credentials, mock_db)

        assert result is None

    @patch('app.infrastructure.auth.dependencies.verify_token')
    def test_get_optional_current_user_inactive_user(self, mock_verify, mock_db, mock_user):
        """Test optional user with inactive user"""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials, credentials="valid.jwt.token")
        mock_payload = {"sub": str(mock_user.id), "email": mock_user.email}
        mock_verify.return_value = mock_payload
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = get_optional_current_user(mock_credentials, mock_db)

        assert result is None


class TestUserToUserInfo:
    """Test user_to_user_info function"""

    def test_user_to_user_info_success(self, mock_user):
        """Test successful UserModel to UserInfo conversion"""
        mock_role1 = Mock()
        mock_role1.role.name = "ADMIN"
        mock_role2 = Mock()
        mock_role2.role.name = "USER"
        mock_user.user_roles = [mock_role1, mock_role2]

        result = user_to_user_info(mock_user)

        assert isinstance(result, UserInfo)
        assert result.id == mock_user.id
        assert result.email == mock_user.email
        assert result.email_verified == mock_user.email_verified
        assert result.is_active == mock_user.is_active
        assert result.roles == ["ADMIN", "USER"]
        assert result.created_at == mock_user.created_at
        assert result.updated_at == mock_user.updated_at

    def test_user_to_user_info_no_roles(self, mock_user):
        """Test UserInfo conversion with no roles"""
        mock_user.user_roles = []

        result = user_to_user_info(mock_user)

        assert result.roles == []


class TestDependenciesIntegration:
    """Integration tests for dependencies"""

    def test_dependencies_can_be_imported(self):
        """Test that all dependency functions can be imported"""
        from app.infrastructure.auth.dependencies import (
            get_current_user, get_current_active_user, get_user_roles,
            require_admin, require_organization, require_auditor,
            require_role, require_any_role, get_optional_current_user,
            user_to_user_info, security, optional_security
        )

        # Test that security schemes are properly initialized
        assert security is not None
        assert optional_security is not None
        assert callable(get_current_user)
        assert callable(require_admin)

    def test_role_requirement_functions_are_callable(self):
        """Test that role requirement functions return callable checkers"""
        admin_checker = require_role("ADMIN")
        assert callable(admin_checker)

        any_role_checker = require_any_role("ADMIN", "USER")
        assert callable(any_role_checker)

    @patch('app.infrastructure.auth.dependencies.verify_token')
    def test_token_verification_called_correctly(self, mock_verify, mock_db, mock_credentials):
        """Test that token verification is called with correct parameters"""
        mock_verify.return_value = None  # Will cause early return in optional user

        get_optional_current_user(mock_credentials, mock_db)

        mock_verify.assert_called_once_with("valid.jwt.token", "access")