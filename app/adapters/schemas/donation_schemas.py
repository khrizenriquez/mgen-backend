"""
Donation API Schemas - Request/Response models
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

from app.domain.entities.donation import DonationStatus


class DonationCreateRequest(BaseModel):
    """Request schema for creating a donation"""
    donor_name: str
    donor_email: EmailStr
    amount: Decimal
    description: Optional[str] = None


class DonationResponse(BaseModel):
    """Response schema for donation data"""
    id: int
    donor_name: str
    donor_email: str
    amount: Decimal
    status: DonationStatus
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    formatted_amount: str

    class Config:
        from_attributes = True


class DonationUpdateRequest(BaseModel):
    """Request schema for updating a donation"""
    description: Optional[str] = None


class DonationListResponse(BaseModel):
    """Response schema for donation list"""
    donations: list[DonationResponse]
    total: int
    limit: int
    offset: int


class DonationStatsResponse(BaseModel):
    """Response schema for donation statistics"""
    total_amount_completed: float
    total_amount_pending: float
    count_completed: int
    count_pending: int
    count_failed: int
    success_rate: float


class DonationStatusUpdate(BaseModel):
    """Schema for updating donation status"""
    status_id: int  # 1=PENDING, 2=APPROVED, 3=DECLINED, 4=EXPIRED