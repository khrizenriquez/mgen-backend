"""
Unit tests for user service
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException

from app.domain.services.user_service import UserService
from app.domain.entities.user import User


@pytest.fixture
def mock_repository():
    """Mock user repository"""
    return Mock()


@pytest.fixture
def user_service(mock_repository):
    """User service instance"""
    return UserService(mock_repository)


@pytest.fixture
def sample_user():
    """Sample user entity"""
    return User(
        id=1,
        email="test@example.com",
        first_name="Test",
        last_name="User",
        is_active=True
    )


class TestUserService:
    """Test user service"""

    @pytest.mark.asyncio
    async def test_get_user_success(self, user_service, mock_repository, sample_user):
        """Test getting user by ID"""
        mock_repository.get_by_id = AsyncMock(return_value=sample_user)
        
        result = await user_service.get_user(1)
        
        assert result is not None
        assert result.id == 1
        assert result.email == "test@example.com"
        mock_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, user_service, mock_repository):
        """Test getting non-existent user"""
        mock_repository.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.get_user(999)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_repository, sample_user):
        """Test creating a new user"""
        mock_repository.get_by_email = AsyncMock(return_value=None)
        mock_repository.create = AsyncMock(return_value=sample_user)
        
        result = await user_service.create_user(sample_user)
        
        assert result is not None
        assert result.email == "test@example.com"
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, mock_repository, sample_user):
        """Test creating user with existing email"""
        mock_repository.get_by_email = AsyncMock(return_value=sample_user)
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(sample_user)
        
        assert exc_info.value.status_code == 400
        assert "already registered" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, user_service, mock_repository):
        """Test creating user with invalid email"""
        invalid_user = User(
            id=1,
            email="invalidemail",
            first_name="Test",
            last_name="User"
        )
        mock_repository.get_by_email = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(invalid_user)
        
        assert exc_info.value.status_code == 400
        assert "invalid email" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_user_success(self, user_service, mock_repository, sample_user):
        """Test updating user"""
        updated_user = User(
            id=1,
            email="test@example.com",
            first_name="Updated",
            last_name="Name"
        )
        mock_repository.get_by_id = AsyncMock(return_value=sample_user)
        mock_repository.get_by_email = AsyncMock(return_value=sample_user)
        mock_repository.update = AsyncMock(return_value=updated_user)
        
        result = await user_service.update_user(1, updated_user)
        
        assert result is not None
        assert result.first_name == "Updated"
        mock_repository.update.assert_called_once_with(1, updated_user)

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_service, mock_repository, sample_user):
        """Test updating non-existent user"""
        mock_repository.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.update_user(999, sample_user)
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_users_list(self, user_service, mock_repository):
        """Test listing users with pagination"""
        mock_users = [Mock(), Mock(), Mock()]
        mock_repository.get_all = AsyncMock(return_value=mock_users)
        
        result = await user_service.get_users(skip=0, limit=10)
        
        assert len(result) == 3
        mock_repository.get_all.assert_called_once_with(skip=0, limit=10)

    @pytest.mark.asyncio
    async def test_get_users_limit_max(self, user_service, mock_repository):
        """Test that limit is capped at 100"""
        mock_repository.get_all = AsyncMock(return_value=[])
        
        await user_service.get_users(skip=0, limit=200)
        
        # Should be called with max limit of 100
        mock_repository.get_all.assert_called_once_with(skip=0, limit=100)

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, mock_repository):
        """Test deleting user"""
        mock_repository.delete = AsyncMock(return_value=True)
        
        result = await user_service.delete_user(1)
        
        assert result is not None
        assert "success" in result["message"].lower()
        mock_repository.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_service, mock_repository):
        """Test deleting non-existent user"""
        mock_repository.delete = AsyncMock(return_value=False)
        
        with pytest.raises(HTTPException) as exc_info:
            await user_service.delete_user(999)
        
        assert exc_info.value.status_code == 404
