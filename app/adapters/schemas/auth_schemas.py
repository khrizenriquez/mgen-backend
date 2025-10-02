"""
Authentication Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's password")
    role: str = Field(default="USER", pattern="^(ADMIN|ORGANIZATION|AUDITOR|DONOR|USER)$", description="User's role (default: USER)")


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(..., description="Refresh token")


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr = Field(..., description="User's email address")


class ResetPasswordRequest(BaseModel):
    """Schema for password reset"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")


class UserInfo(BaseModel):
    """Schema for user information in responses"""
    id: UUID = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    email_verified: bool = Field(..., description="Whether email is verified")
    is_active: bool = Field(default=True, description="Whether the user is active")
    roles: List[str] = Field(..., description="User's roles")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")

    class Config:
        from_attributes = True


class RoleInfo(BaseModel):
    """Schema for role information"""
    id: int = Field(..., description="Role's unique identifier")
    name: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Role description")

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    """Schema for dashboard data"""
    user: UserInfo = Field(..., description="User information")
    stats: dict = Field(..., description="Dashboard statistics based on role")
    recent_activity: List[dict] = Field(default_factory=list, description="Recent user activity")


class PasswordChangeRequest(BaseModel):
    """Schema for password change"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")


class EmailVerificationRequest(BaseModel):
    """Schema for email verification"""
    token: str = Field(..., description="Email verification token")


class UserListResponse(BaseModel):
    """Schema for paginated user list response"""
    users: List[UserInfo] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    skip: int = Field(..., description="Number of skipped records")
    limit: int = Field(..., description="Maximum number of records returned")


class GenericResponse(BaseModel):
    """Generic success response"""
    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Success status")