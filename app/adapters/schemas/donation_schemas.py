"""
Donation API Schemas - Request/Response models
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, EmailStr, validator

from app.domain.entities.donation import DonationStatus, DonationType


class DonationCreateRequest(BaseModel):
    """Request schema for creating a donation"""
    donor_name: str
    donor_email: EmailStr
    amount: Decimal
    currency: str
    donation_type: DonationType
    description: Optional[str] = None
    
    @validator('donor_name')
    def validate_donor_name(cls, v):
        if not v.strip():
            raise ValueError('Donor name cannot be empty')
        return v.strip()
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        if len(v) != 3:
            raise ValueError('Currency must be 3 characters')
        return v.upper()


class DonationResponse(BaseModel):
    """Response schema for donation data"""
    id: int
    donor_name: str
    donor_email: str
    amount: Decimal
    currency: str
    donation_type: DonationType
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