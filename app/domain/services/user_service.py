"""
User service with business logic
"""
from typing import List, Optional
from fastapi import HTTPException, status

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository


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