"""
Unit tests for organization service
"""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from fastapi import HTTPException

from app.domain.services.organization_service import OrganizationService
from app.adapters.schemas.organization_schemas import (
    OrganizationCreate, OrganizationUpdate, OrganizationSummary
)


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def organization_service(mock_db):
    """Organization service instance"""
    return OrganizationService(mock_db)


@pytest.fixture
def mock_organization():
    """Mock organization"""
    org = Mock()
    org.id = uuid4()
    org.name = "Test Organization"
    org.description = "Test Description"
    org.contact_email = "contact@test.org"
    org.contact_phone = "+1234567890"
    org.address = "123 Test St"
    org.website = "https://test.org"
    org.is_active = True
    return org


@pytest.fixture
def organization_create_data():
    """Organization create data"""
    return OrganizationCreate(
        name="New Organization",
        description="New Description",
        contact_email="contact@new.org",
        contact_phone="+0987654321",
        address="456 New St",
        website="https://new.org",
        is_active=True
    )


@pytest.fixture
def organization_update_data():
    """Organization update data"""
    return OrganizationUpdate(
        name="Updated Organization",
        description="Updated Description",
        contact_email="updated@org.com",
        is_active=False
    )


class TestCreateOrganization:
    """Test create organization"""

    def test_create_organization_success(self, organization_service, mock_db, organization_create_data):
        """Test successful organization creation"""
        # Mock no existing organization
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock organization creation
        mock_created_org = Mock()
        mock_created_org.id = uuid4()
        mock_created_org.name = organization_create_data.name

        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', mock_created_org.id))

        result = organization_service.create_organization(organization_create_data)

        assert result.name == organization_create_data.name
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_organization_duplicate_name(self, organization_service, mock_db, organization_create_data):
        """Test creating organization with duplicate name"""
        # Mock existing organization
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()

        with pytest.raises(HTTPException) as exc_info:
            organization_service.create_organization(organization_create_data)

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail.lower()


class TestGetOrganization:
    """Test get organization"""

    def test_get_organization_success(self, organization_service, mock_db, mock_organization):
        """Test getting organization by ID"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_organization

        result = organization_service.get_organization(mock_organization.id)

        assert result.id == mock_organization.id
        assert result.name == mock_organization.name

    def test_get_organization_not_found(self, organization_service, mock_db):
        """Test getting non-existent organization"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            organization_service.get_organization(uuid4())

        assert exc_info.value.status_code == 404


class TestGetOrganizations:
    """Test get organizations list"""

    def test_get_organizations_success(self, organization_service, mock_db):
        """Test getting organizations list"""
        mock_orgs = [Mock(), Mock(), Mock()]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_orgs

        result = organization_service.get_organizations(skip=10, limit=20)

        assert len(result) == 3

    def test_get_organizations_default_params(self, organization_service, mock_db):
        """Test getting organizations with default parameters"""
        mock_orgs = [Mock(), Mock()]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_orgs

        result = organization_service.get_organizations()

        assert len(result) == 2


class TestUpdateOrganization:
    """Test update organization"""

    def test_update_organization_success(self, organization_service, mock_db, mock_organization, organization_update_data):
        """Test successful organization update"""
        # Mock query to return organization twice: once for get_organization, once for name check
        def query_side_effect(*args):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = mock_organization
            return mock_query
        
        mock_db.query.side_effect = [
            query_side_effect(),  # First call: get_organization
            query_side_effect(),  # Second call: check name existence (returns same org, so no conflict)
        ]
        
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        result = organization_service.update_organization(mock_organization.id, organization_update_data)

        assert result.name == organization_update_data.name
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_organization_not_found(self, organization_service, mock_db, organization_update_data):
        """Test updating non-existent organization"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            organization_service.update_organization(uuid4(), organization_update_data)

        assert exc_info.value.status_code == 404


class TestDeleteOrganization:
    """Test delete organization"""

    def test_delete_organization_success(self, organization_service, mock_db, mock_organization):
        """Test successful organization deletion"""
        # Mock multiple query calls
        call_count = [0]
        
        def query_side_effect(*args):
            call_count[0] += 1
            mock_query = Mock()
            if call_count[0] == 1:
                # First call: get_organization
                mock_query.filter.return_value.first.return_value = mock_organization
            else:
                # Second call: count users
                mock_query.filter.return_value.count.return_value = 0
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        mock_db.delete = Mock()
        mock_db.commit = Mock()

        result = organization_service.delete_organization(mock_organization.id)

        assert result["message"] == "Organization deleted successfully"
        mock_db.delete.assert_called_once_with(mock_organization)
        mock_db.commit.assert_called_once()

    def test_delete_organization_not_found(self, organization_service, mock_db):
        """Test deleting non-existent organization"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            organization_service.delete_organization(uuid4())

        assert exc_info.value.status_code == 404


class TestGetOrganizationSummary:
    """Test get organization summary"""

    def test_get_organization_summary_success(self, organization_service, mock_db, mock_organization):
        """Test getting organization summary"""
        # Mock multiple query calls
        call_count = [0]
        
        def query_side_effect(*args):
            call_count[0] += 1
            mock_query = Mock()
            
            if call_count[0] == 1:
                # First call: get_organization
                mock_query.filter.return_value.first.return_value = mock_organization
            elif call_count[0] == 2:
                # Second call: count users
                mock_query.filter.return_value.count.return_value = 5
            elif call_count[0] == 3:
                # Third call: subquery for user IDs (used in .in_())
                mock_subquery = Mock()
                mock_subquery.filter.return_value = mock_subquery
                return mock_subquery
            elif call_count[0] == 4:
                # Fourth call: count donations with .in_()
                mock_filter = Mock()
                mock_filter.count.return_value = 10
                mock_query.filter.return_value = mock_filter
            elif call_count[0] == 5:
                # Fifth call: subquery for user IDs again
                mock_subquery = Mock()
                mock_subquery.filter.return_value = mock_subquery
                return mock_subquery
            else:
                # Sixth call: sum donations with .in_()
                mock_filter = Mock()
                mock_filter.filter.return_value = mock_filter
                mock_filter.scalar.return_value = 500.00
                mock_query.filter.return_value = mock_filter
            
            return mock_query
        
        mock_db.query.side_effect = query_side_effect

        result = organization_service.get_organization_summary(mock_organization.id)

        assert isinstance(result, OrganizationSummary)
        assert result.name == mock_organization.name
        assert result.total_users == 5
        assert result.total_donations == 10
        assert result.total_amount == 500.00

    def test_get_organization_summary_not_found(self, organization_service, mock_db):
        """Test getting summary for non-existent organization"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            organization_service.get_organization_summary(uuid4())

        assert exc_info.value.status_code == 404


class TestGetAllOrganizationSummaries:
    """Test get all organization summaries"""

    def test_get_all_organization_summaries_success(self, organization_service, mock_db):
        """Test getting all organization summaries"""
        from unittest.mock import patch
        
        # Create mock organizations
        mock_org1 = Mock()
        mock_org1.id = uuid4()
        mock_org1.name = "Org 1"
        
        mock_org2 = Mock()
        mock_org2.id = uuid4()
        mock_org2.name = "Org 2"
        
        mock_orgs = [mock_org1, mock_org2]
        
        # Create mock summaries
        mock_summary1 = OrganizationSummary(
            id=mock_org1.id,
            name="Org 1",
            total_users=5,
            total_donations=10,
            total_amount=1000.00
        )
        
        mock_summary2 = OrganizationSummary(
            id=mock_org2.id,
            name="Org 2",
            total_users=3,
            total_donations=7,
            total_amount=750.00
        )
        
        # Mock get_organizations to return mock_orgs
        # Mock get_organization_summary to return appropriate summaries
        with patch.object(organization_service, 'get_organizations', return_value=mock_orgs):
            with patch.object(organization_service, 'get_organization_summary', side_effect=[mock_summary1, mock_summary2]):
                result = organization_service.get_all_organization_summaries()

                assert isinstance(result, list)
                assert len(result) == 2
                assert result[0].name == "Org 1"
                assert result[1].name == "Org 2"


class TestOrganizationServiceIntegration:
    """Integration tests for organization service"""

    def test_service_initialization(self, mock_db):
        """Test service can be initialized"""
        service = OrganizationService(mock_db)
        assert service.db == mock_db

    def test_service_handles_db_errors(self, organization_service, mock_db, organization_create_data):
        """Test service handles database errors gracefully"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            organization_service.create_organization(organization_create_data)