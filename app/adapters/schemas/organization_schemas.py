"""
Organization Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional
from datetime import datetime
from uuid import UUID


class OrganizationBase(BaseModel):
    """Base organization schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Contact phone")
    address: Optional[str] = Field(None, max_length=500, description="Organization address")
    website: Optional[HttpUrl] = Field(None, description="Organization website")
    is_active: bool = Field(default=True, description="Whether the organization is active")


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization"""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an existing organization"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Organization name")
    description: Optional[str] = Field(None, max_length=1000, description="Organization description")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Contact phone")
    address: Optional[str] = Field(None, max_length=500, description="Organization address")
    website: Optional[HttpUrl] = Field(None, description="Organization website")
    is_active: Optional[bool] = Field(None, description="Whether the organization is active")


class OrganizationResponse(OrganizationBase):
    """Schema for organization response"""
    id: UUID = Field(..., description="Organization's unique identifier")
    created_at: datetime = Field(..., description="Organization creation timestamp")
    updated_at: datetime = Field(..., description="Organization last update timestamp")

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """Schema for paginated organization list response"""
    organizations: list[OrganizationResponse] = Field(..., description="List of organizations")
    total: int = Field(..., description="Total number of organizations")
    skip: int = Field(..., description="Number of skipped records")
    limit: int = Field(..., description="Maximum number of records returned")


class OrganizationSummary(BaseModel):
    """Schema for organization summary (used in dashboards)"""
    id: UUID = Field(..., description="Organization's unique identifier")
    name: str = Field(..., description="Organization name")
    total_users: int = Field(..., description="Total users in organization")
    total_donations: int = Field(..., description="Total donations from organization")
    total_amount: float = Field(..., description="Total donation amount")

    class Config:
        from_attributes = True