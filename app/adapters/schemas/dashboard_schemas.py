"""
Dashboard Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class UserSummary(BaseModel):
    """Schema for user summary in dashboard"""
    id: str = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    roles: List[str] = Field(..., description="User's roles")
    joined_at: datetime = Field(..., description="User registration date")
    status: str = Field(..., description="User status")


class DonationSummary(BaseModel):
    """Schema for donation summary in dashboard"""
    id: str = Field(..., description="Donation's unique identifier")
    amount_gtq: float = Field(..., description="Donation amount in GTQ")
    donor_email: str = Field(..., description="Donor's email")
    donor_name: Optional[str] = Field(None, description="Donor's name")
    status: str = Field(..., description="Donation status")
    created_at: datetime = Field(..., description="Donation creation date")


class DashboardStats(BaseModel):
    """Schema for dashboard statistics"""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    total_donations: int = Field(..., description="Total number of donations")
    total_amount_gtq: float = Field(..., description="Total donation amount in GTQ")
    pending_donations: int = Field(..., description="Number of pending donations")
    recent_users: List[UserSummary] = Field(..., description="Recent user registrations")
    recent_donations: List[DonationSummary] = Field(..., description="Recent donations")


class DonorDashboardStats(BaseModel):
    """Schema for donor-specific dashboard statistics"""
    total_donations: int = Field(..., description="Total donations made by user")
    total_amount_gtq: float = Field(..., description="Total amount donated by user")
    monthly_average: float = Field(..., description="Monthly average donation amount")
    favorite_program: Optional[str] = Field(None, description="Most donated program")
    member_since: datetime = Field(..., description="User registration date")
    donation_streak: int = Field(..., description="Current donation streak in months")
    my_donations: List[DonationSummary] = Field(..., description="User's recent donations")


class UserDashboardStats(BaseModel):
    """Schema for regular user dashboard statistics"""
    total_donations: int = Field(..., description="Total donations in system")
    total_amount_gtq: float = Field(..., description="Total donation amount in system")
    member_since: datetime = Field(..., description="User registration date")


class DashboardResponse(BaseModel):
    """Generic dashboard response"""
    stats: Dict[str, Any] = Field(..., description="Dashboard statistics")
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list, description="Recent activity items")