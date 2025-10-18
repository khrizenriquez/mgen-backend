"""
User service with business logic
"""
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from datetime import datetime

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.auth.jwt_utils import verify_password, get_password_hash


class UserService:
    """User service with business logic"""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def create_user(self, user: User) -> User:
        """Create a new user"""
        # Check if email already exists
        existing_user = await self.user_repository.get_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Validate email format (basic validation)
        if "@" not in user.email or "." not in user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )

        return await self.user_repository.create(user)

    async def get_user(self, user_id: int) -> User:
        """Get user by ID"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def get_users(self, skip: int = 0, limit: int = 100, organization_id: Optional[str] = None) -> List[User]:
        """Get all users with pagination and optional organization filtering"""
        if limit > 100:
            limit = 100  # Max limit
        return await self.user_repository.get_all(skip=skip, limit=limit, organization_id=organization_id)

    async def update_user(self, user_id: int, user: User) -> User:
        """Update user"""
        # Check if user exists
        existing_user = await self.user_repository.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if email is being changed and if it's already taken
        if user.email != existing_user.email:
            email_user = await self.user_repository.get_by_email(user.email)
            if email_user and email_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # Validate email format
        if "@" not in user.email or "." not in user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )

        updated_user = await self.user_repository.update(user_id, user)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user

    async def delete_user(self, user_id: int) -> dict:
        """Delete user"""
        success = await self.user_repository.delete(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {"message": "User deleted successfully"}

    async def update_profile(self, user_id: int, profile_data: Dict[str, Any]) -> User:
        """Update user profile (first_name, last_name, phone, address)"""
        # Check if user exists
        existing_user = await self.user_repository.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update only profile fields
        update_data = {}
        if 'first_name' in profile_data and profile_data['first_name'] is not None:
            update_data['first_name'] = profile_data['first_name']
        if 'last_name' in profile_data and profile_data['last_name'] is not None:
            update_data['last_name'] = profile_data['last_name']
        if 'phone' in profile_data and profile_data['phone'] is not None:
            update_data['phone'] = profile_data['phone']
        if 'address' in profile_data and profile_data['address'] is not None:
            update_data['address'] = profile_data['address']

        updated_user = await self.user_repository.update_profile(user_id, update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user

    async def change_password(self, user_id: int, current_password: str, new_password: str) -> dict:
        """Change user password"""
        # Get user with password hash
        user = await self.user_repository.get_by_id_with_password(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Hash new password
        hashed_password = get_password_hash(new_password)

        # Update password
        success = await self.user_repository.update_password(user_id, hashed_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )

        return {"message": "Password changed successfully"}

    async def update_preferences(self, user_id: int, preferences: Dict[str, Any]) -> User:
        """Update user preferences"""
        # Check if user exists
        existing_user = await self.user_repository.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        updated_user = await self.user_repository.update_preferences(user_id, preferences)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user

    async def get_user_profile(self, user_id: int) -> User:
        """Get complete user profile"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user