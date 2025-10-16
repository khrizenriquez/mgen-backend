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


class GrowthMetrics(BaseModel):
    """Schema for growth metrics"""
    users_growth_percentage: float = Field(..., description="User growth percentage vs previous month")
    donations_growth_percentage: float = Field(..., description="Donations growth percentage vs previous month")
    amount_growth_percentage: float = Field(..., description="Amount growth percentage vs previous month")
    current_month: Dict[str, Any] = Field(..., description="Current month metrics")
    previous_month: Dict[str, Any] = Field(..., description="Previous month metrics")


class DashboardStats(BaseModel):
    """Schema for dashboard statistics"""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    total_donations: int = Field(..., description="Total number of donations")
    total_amount_gtq: float = Field(..., description="Total donation amount in GTQ")
    pending_donations: int = Field(..., description="Number of pending donations")
    system_health: int = Field(..., description="System health percentage")
    recent_users: List[UserSummary] = Field(..., description="Recent user registrations")
    recent_donations: List[DonationSummary] = Field(..., description="Recent donations")
    growth_metrics: GrowthMetrics = Field(..., description="Growth metrics vs previous period")


class ImpactMetrics(BaseModel):
    """Schema for impact metrics"""
    children_impacted: int = Field(..., description="Number of children impacted")
    meals_provided: int = Field(..., description="Number of meals provided")
    scholarships_awarded: int = Field(..., description="Number of scholarships awarded")
    evangelism_hours: int = Field(..., description="Hours of evangelism provided")


class ActiveProgram(BaseModel):
    """Schema for active program"""
    id: str = Field(..., description="Program unique identifier")
    name: str = Field(..., description="Program name")
    description: str = Field(..., description="Program description")
    goal_amount: float = Field(..., description="Fundraising goal amount")
    current_amount: float = Field(..., description="Current raised amount")
    progress_percentage: int = Field(..., description="Progress percentage")
    start_date: str = Field(..., description="Program start date")
    end_date: str = Field(..., description="Program end date")
    status: str = Field(..., description="Program status")


class UpcomingEvent(BaseModel):
    """Schema for upcoming event"""
    id: str = Field(..., description="Event unique identifier")
    title: str = Field(..., description="Event title")
    date: str = Field(..., description="Event date")
    type: str = Field(..., description="Event type")
    description: str = Field(..., description="Event description")
    location: str = Field(..., description="Event location")
    status: str = Field(..., description="Event status")


class UserPreferences(BaseModel):
    """Schema for user preferences"""
    favorite_cause: str = Field(..., description="User's favorite cause")
    communication_preferences: Dict[str, Any] = Field(..., description="Communication preferences")
    privacy_settings: Dict[str, Any] = Field(..., description="Privacy settings")


class UserLevels(BaseModel):
    """Schema for user level information"""
    current_level: str = Field(..., description="Current user level")
    current_level_color: str = Field(..., description="Color for current level")
    next_level: Optional[str] = Field(None, description="Next level to achieve")
    total_donated: float = Field(..., description="Total amount donated")
    progress_percentage: float = Field(..., description="Progress to next level")
    next_level_threshold: float = Field(..., description="Threshold for next level")
    amount_needed: float = Field(..., description="Amount needed to reach next level")


class DonorDashboardStats(BaseModel):
    """Schema for donor-specific dashboard statistics"""
    total_donations: int = Field(..., description="Total donations made by user")
    total_amount_gtq: float = Field(..., description="Total amount donated by user")
    monthly_average: float = Field(..., description="Monthly average donation amount")
    favorite_program: Optional[str] = Field(None, description="Most donated program")
    impact_children: int = Field(..., description="Number of children impacted by user's donations")
    member_since: datetime = Field(..., description="User registration date")
    donation_streak: int = Field(..., description="Current donation streak in months")
    next_reward: str = Field(..., description="Next reward level")
    my_donations: List[DonationSummary] = Field(..., description="User's recent donations")


class UserDashboardStats(BaseModel):
    """Schema for regular user dashboard statistics"""
    total_donations: int = Field(..., description="Total donations made by user")
    total_amount_gtq: float = Field(..., description="Total donation amount by user")
    favorite_cause: str = Field(..., description="User's favorite cause")
    member_since: datetime = Field(..., description="User registration date")
    next_milestone: float = Field(..., description="Next milestone amount")
    current_progress: float = Field(..., description="Current progress towards milestone")


class DashboardResponse(BaseModel):
    """Generic dashboard response"""
    stats: Dict[str, Any] = Field(..., description="Dashboard statistics")
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list, description="Recent activity items")