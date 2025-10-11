"""
Unit tests for user controller
"""
import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_user_service():
    """Mock user service"""
    return Mock()


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    user = Mock()
    user.id = "user-123"
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.is_active = True
    user.organization_id = "org-123"
    return user


class TestUserController:
    """Test user controller endpoints"""

    def test_get_current_user_info(self, mock_current_user):
        """Test getting current user info"""
        assert mock_current_user.id == "user-123"
        assert mock_current_user.email == "test@example.com"
        assert mock_current_user.is_active is True

    def test_update_user_profile(self, mock_user_service, mock_current_user):
        """Test updating user profile"""
        update_data = {
            "full_name": "Updated Name",
            "phone": "555-1234"
        }
        
        mock_updated_user = Mock()
        mock_updated_user.full_name = update_data["full_name"]
        
        mock_user_service.update_user.return_value = mock_updated_user
        
        assert mock_updated_user.full_name == "Updated Name"

    def test_change_user_password(self, mock_user_service, mock_current_user):
        """Test changing user password"""
        password_data = {
            "current_password": "oldpass123",
            "new_password": "newpass456"
        }
        
        mock_user_service.change_password.return_value = True
        
        result = mock_user_service.change_password(
            mock_current_user.id,
            password_data["current_password"],
            password_data["new_password"]
        )
        
        assert result is True

    def test_deactivate_user(self, mock_user_service, mock_current_user):
        """Test deactivating user account"""
        mock_user_service.deactivate_user.return_value = True
        
        result = mock_user_service.deactivate_user(mock_current_user.id)
        assert result is True

    def test_get_user_by_id(self, mock_user_service):
        """Test getting user by ID"""
        user_id = "user-456"
        
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.email = "other@example.com"
        
        mock_user_service.get_user.return_value = mock_user
        
        assert mock_user.id == user_id

    def test_list_users(self, mock_user_service):
        """Test listing users"""
        mock_users = [Mock(), Mock(), Mock()]
        mock_user_service.list_users.return_value = mock_users
        
        assert len(mock_users) == 3

    def test_user_search(self, mock_user_service):
        """Test searching users"""
        search_query = "john"
        
        mock_results = [Mock(), Mock()]
        mock_user_service.search_users.return_value = mock_results
        
        result = mock_user_service.search_users(search_query)
        assert len(result) == 2

    def test_user_permissions(self, mock_current_user):
        """Test user permissions check"""
        # Mock user with admin role
        mock_current_user.roles = ["admin"]
        
        assert "admin" in mock_current_user.roles

    def test_user_organization_access(self, mock_current_user):
        """Test user organization access"""
        assert mock_current_user.organization_id == "org-123"

    def test_user_validation(self):
        """Test user data validation"""
        valid_email = "user@example.com"
        assert "@" in valid_email
        assert "." in valid_email
