"""
Unit tests for database seeders
"""
import pytest
from unittest.mock import Mock, patch, call
from uuid import UUID

from app.infrastructure.database.seeders import (
    seed_roles, seed_organization, seed_default_users, run_seeders
)


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


class TestSeedRoles:
    """Test seed roles function"""

    def test_seed_roles_creates_missing_roles(self, mock_db):
        """Test that seed_roles creates roles that don't exist"""
        # Mock that no roles exist initially
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        seed_roles(mock_db)

        # Should have added 5 roles
        assert mock_db.add.call_count == 5
        mock_db.commit.assert_called_once()

    def test_seed_roles_skips_existing_roles(self, mock_db):
        """Test that seed_roles skips roles that already exist"""
        # Mock that all roles already exist
        mock_existing_role = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_existing_role
        mock_db.query.return_value = mock_query

        seed_roles(mock_db)

        # Should not add any roles
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()

    def test_seed_roles_creates_correct_role_data(self, mock_db):
        """Test that seed_roles creates roles with correct data"""
        # Mock that no roles exist
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        seed_roles(mock_db)

        # Check that add was called for each role
        add_calls = mock_db.add.call_args_list
        assert len(add_calls) == 5

        # Check role names were created
        role_names = [call[0][0].name for call in add_calls]
        expected_roles = ["ADMIN", "ORGANIZATION", "AUDITOR", "DONOR", "USER"]
        assert set(role_names) == set(expected_roles)


class TestSeedOrganization:
    """Test seed organization function"""

    def test_seed_organization_creates_missing_org(self, mock_db):
        """Test that seed_organization creates org that doesn't exist"""
        # Mock that organization doesn't exist
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        seed_organization(mock_db)

        # Should add organization
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_seed_organization_skips_existing_org(self, mock_db):
        """Test that seed_organization skips org that already exists"""
        # Mock that organization already exists
        mock_existing_org = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_existing_org
        mock_db.query.return_value = mock_query

        seed_organization(mock_db)

        # Should not add organization
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_seed_organization_creates_correct_org_data(self, mock_db):
        """Test that seed_organization creates org with correct data"""
        # Mock that organization doesn't exist
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        seed_organization(mock_db)

        # Check organization data
        org_call = mock_db.add.call_args[0][0]
        assert org_call.name == "Fundación Donaciones Guatemala"
        assert org_call.contact_email == "contacto@donacionesgt.org"
        assert org_call.is_active is True
        assert str(org_call.id) == "550e8400-e29b-41d4-a716-446655440000"


class TestSeedDefaultUsers:
    """Test seed default users function"""

    @patch('app.infrastructure.database.seeders.seed_organization')
    @patch('app.infrastructure.database.seeders.seed_roles')
    @patch('app.infrastructure.database.seeders.get_password_hash')
    def test_seed_default_users_creates_missing_users(self, mock_hash, mock_seed_roles, mock_seed_org, mock_db):
        """Test that seed_default_users creates users that don't exist"""
        mock_hash.return_value = "hashed_password"

        # Mock roles
        mock_admin_role = Mock()
        mock_admin_role.name = "ADMIN"
        mock_donor_role = Mock()
        mock_donor_role.name = "DONOR"
        mock_user_role = Mock()
        mock_user_role.name = "USER"

        # Mock query to return roles first, then no existing users
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'RoleModel':
                # Return roles in order: ADMIN, DONOR, USER
                mock_query.filter.return_value.first.side_effect = [
                    mock_admin_role, mock_donor_role, mock_user_role
                ]
            else:  # UserModel
                # No existing users
                mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect

        seed_default_users(mock_db)

        # Should add users and user roles
        assert mock_db.add.call_count >= 3  # At least 3 users and their roles
        assert mock_db.commit.call_count >= 1

    @patch('app.infrastructure.database.seeders.seed_organization')
    @patch('app.infrastructure.database.seeders.seed_roles')
    @patch('app.infrastructure.database.seeders.get_password_hash')
    def test_seed_default_users_skips_existing_users(self, mock_hash, mock_seed_roles, mock_seed_org, mock_db):
        """Test that seed_default_users skips users that already exist"""
        mock_hash.return_value = "hashed_password"

        # Mock roles
        mock_admin_role = Mock()
        mock_admin_role.name = "ADMIN"
        mock_donor_role = Mock()
        mock_donor_role.name = "DONOR"
        mock_user_role = Mock()
        mock_user_role.name = "USER"

        # Mock that users already exist
        mock_existing_user = Mock()
        
        # Mock query to return roles first, then existing users
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'RoleModel':
                mock_query.filter.return_value.first.side_effect = [
                    mock_admin_role, mock_donor_role, mock_user_role
                ]
            else:  # UserModel
                mock_query.filter.return_value.first.return_value = mock_existing_user
            return mock_query
        
        mock_db.query.side_effect = query_side_effect

        seed_default_users(mock_db)

        # Should not add any users
        mock_db.add.assert_not_called()

    @patch('app.infrastructure.database.seeders.seed_organization')
    @patch('app.infrastructure.database.seeders.seed_roles')
    @patch('app.infrastructure.database.seeders.get_password_hash')
    def test_seed_default_users_creates_admin_user(self, mock_hash, mock_seed_roles, mock_seed_org, mock_db):
        """Test that seed_default_users creates admin user with correct data"""
        mock_hash.return_value = "hashed_password"

        # Mock roles
        mock_admin_role = Mock()
        mock_admin_role.name = "ADMIN"
        mock_donor_role = Mock()
        mock_donor_role.name = "DONOR"
        mock_user_role = Mock()
        mock_user_role.name = "USER"

        # Mock query to return roles first, then no existing users
        def query_side_effect(model):
            mock_query = Mock()
            if model.__name__ == 'RoleModel':
                mock_query.filter.return_value.first.side_effect = [
                    mock_admin_role, mock_donor_role, mock_user_role
                ]
            else:  # UserModel
                mock_query.filter.return_value.first.return_value = None
            return mock_query
        
        mock_db.query.side_effect = query_side_effect

        seed_default_users(mock_db)

        # Check that admin user was created
        add_calls = mock_db.add.call_args_list
        admin_user_call = None
        for call_args in add_calls:
            if hasattr(call_args[0][0], 'email') and call_args[0][0].email == "adminseminario@test.com":
                admin_user_call = call_args[0][0]
                break

        assert admin_user_call is not None, "Admin user should have been created"
        # UserModel only has email, password_hash, email_verified, is_active fields
        assert admin_user_call.email == "adminseminario@test.com"
        assert admin_user_call.email_verified == True
        assert admin_user_call.is_active == True


class TestRunSeeders:
    """Test run seeders function"""

    @patch('app.infrastructure.database.seeders.seed_roles')
    @patch('app.infrastructure.database.seeders.seed_organization')
    @patch('app.infrastructure.database.seeders.seed_default_users')
    def test_run_seeders_calls_all_seeders(self, mock_seed_users, mock_seed_org, mock_seed_roles, mock_db):
        """Test that run_seeders calls all individual seeder functions"""
        run_seeders(mock_db)

        mock_seed_roles.assert_called_once_with(mock_db)
        mock_seed_org.assert_called_once_with(mock_db)
        mock_seed_users.assert_called_once_with(mock_db)

    @patch('app.infrastructure.database.seeders.seed_roles')
    @patch('app.infrastructure.database.seeders.seed_organization')
    @patch('app.infrastructure.database.seeders.seed_default_users')
    def test_run_seeders_handles_exceptions(self, mock_seed_users, mock_seed_org, mock_seed_roles, mock_db):
        """Test that run_seeders handles exceptions and rolls back"""
        mock_seed_roles.side_effect = Exception("Role seeding failed")

        # Should raise the exception
        with pytest.raises(Exception, match="Role seeding failed"):
            run_seeders(mock_db)

        # Database rollback should be called
        mock_db.rollback.assert_called_once()


class TestSeedersIntegration:
    """Integration tests for seeders"""

    def test_seeders_can_be_imported(self):
        """Test that all seeder functions can be imported"""
        from app.infrastructure.database.seeders import (
            seed_roles, seed_organization, seed_default_users, run_seeders
        )

        assert callable(seed_roles)
        assert callable(seed_organization)
        assert callable(seed_default_users)
        assert callable(run_seeders)

    @patch('app.infrastructure.database.seeders.logger')
    def test_seeders_log_appropriate_messages(self, mock_logger, mock_db):
        """Test that seeders log appropriate messages"""
        # Mock that no data exists
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        seed_roles(mock_db)

        # Should have logged role creation messages
        assert mock_logger.info.call_count >= 5  # One for each role