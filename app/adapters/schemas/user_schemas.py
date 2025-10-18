"""
User Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    is_active: bool = Field(default=True, description="Whether the user is active")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    pass


class UserUpdate(UserBase):
    """Schema for updating an existing user"""
    pass


class UserResponse(UserBase):
    """Schema for user response"""
    id: int = Field(..., description="User's unique identifier")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")

    class Config:
        from_attributes = True

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()


class UserListResponse(BaseModel):
    """Schema for paginated user list response"""
    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users (if available)")
    skip: int = Field(..., description="Number of skipped records")
    limit: int = Field(..., description="Maximum number of records returned")


class DeleteResponse(BaseModel):
    """Schema for delete operation response"""
    message: str = Field(..., description="Success message")


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's last name")
    phone: Optional[str] = Field(None, max_length=20, description="User's phone number")
    address: Optional[str] = Field(None, max_length=255, description="User's address")


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    id: int = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    phone: Optional[str] = Field(None, description="User's phone number")
    address: Optional[str] = Field(None, description="User's address")
    is_active: bool = Field(..., description="Whether the user is active")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Schema for password change request"""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences"""
    communication_preferences: Optional[dict] = Field(None, description="Communication preferences")
    privacy_settings: Optional[dict] = Field(None, description="Privacy settings")


class UserPreferencesResponse(BaseModel):
    """Schema for user preferences response"""
    favorite_cause: str = Field(..., description="User's favorite cause")
    communication_preferences: dict = Field(..., description="Communication preferences")
    privacy_settings: dict = Field(..., description="Privacy settings")