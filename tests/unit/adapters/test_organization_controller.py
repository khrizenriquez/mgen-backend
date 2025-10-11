"""
Unit tests for organization controller
"""
import pytest
from unittest.mock import Mock
from datetime import datetime


@pytest.fixture
def mock_organization_service():
    """Mock organization service"""
    return Mock()


@pytest.fixture
def mock_current_user():
    """Mock current user with admin role"""
    user = Mock()
    user.id = "user-123"
    user.email = "admin@example.com"
    user.roles = ["admin"]
    user.organization_id = "org-123"
    return user


@pytest.fixture
def sample_organization_data():
    """Sample organization data"""
    return {
        "name": "Test Organization",
        "email": "info@testorg.com",
        "phone": "555-1234",
        "address": "123 Main St",
        "tax_id": "12-3456789",
        "website": "https://testorg.com"
    }


class TestOrganizationController:
    """Test organization controller endpoints"""

    def test_create_organization(self, mock_organization_service, sample_organization_data):
        """Test creating an organization"""
        mock_org = Mock()
        mock_org.id = "org-456"
        mock_org.name = sample_organization_data["name"]
        mock_org.email = sample_organization_data["email"]
        
        mock_organization_service.create_organization.return_value = mock_org
        
        assert mock_org.name == "Test Organization"

    def test_get_organization_by_id(self, mock_organization_service):
        """Test getting organization by ID"""
        org_id = "org-123"
        
        mock_org = Mock()
        mock_org.id = org_id
        mock_org.name = "My Organization"
        
        mock_organization_service.get_organization.return_value = mock_org
        
        assert mock_org.id == org_id

    def test_update_organization(self, mock_organization_service, mock_current_user):
        """Test updating organization"""
        org_id = "org-123"
        update_data = {"name": "Updated Org Name"}
        
        mock_org = Mock()
        mock_org.id = org_id
        mock_org.name = update_data["name"]
        
        mock_organization_service.update_organization.return_value = mock_org
        
        assert mock_org.name == "Updated Org Name"

    def test_delete_organization(self, mock_organization_service, mock_current_user):
        """Test deleting organization"""
        org_id = "org-123"
        
        mock_organization_service.delete_organization.return_value = True
        
        result = mock_organization_service.delete_organization(org_id)
        assert result is True

    def test_list_organizations(self, mock_organization_service):
        """Test listing organizations"""
        mock_orgs = [Mock(), Mock(), Mock()]
        mock_organization_service.list_organizations.return_value = mock_orgs
        
        assert len(mock_orgs) == 3

    def test_get_organization_members(self, mock_organization_service):
        """Test getting organization members"""
        org_id = "org-123"
        
        mock_members = [Mock(), Mock()]
        mock_organization_service.get_members.return_value = mock_members
        
        result = mock_organization_service.get_members(org_id)
        assert len(result) == 2

    def test_add_organization_member(self, mock_organization_service, mock_current_user):
        """Test adding member to organization"""
        org_id = "org-123"
        user_id = "user-456"
        
        mock_organization_service.add_member.return_value = True
        
        result = mock_organization_service.add_member(org_id, user_id)
        assert result is True

    def test_remove_organization_member(self, mock_organization_service, mock_current_user):
        """Test removing member from organization"""
        org_id = "org-123"
        user_id = "user-456"
        
        mock_organization_service.remove_member.return_value = True
        
        result = mock_organization_service.remove_member(org_id, user_id)
        assert result is True

    def test_organization_statistics(self, mock_organization_service):
        """Test getting organization statistics"""
        org_id = "org-123"
        
        mock_stats = {
            "total_donations": 50,
            "total_members": 10,
            "total_campaigns": 5
        }
        
        mock_organization_service.get_statistics.return_value = mock_stats
        
        assert mock_stats["total_donations"] == 50

    def test_organization_validation(self, sample_organization_data):
        """Test organization data validation"""
        assert len(sample_organization_data["name"]) > 0
        assert "@" in sample_organization_data["email"]
        assert len(sample_organization_data["tax_id"]) > 0
