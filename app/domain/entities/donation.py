"""
Donation Entity - Core business model
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


class DonationStatus(Enum):
    """Donation status enumeration - maps to status_catalog table"""
    PENDING = 1      # donation.pending
    APPROVED = 2     # donation.approved  
    DECLINED = 3     # donation.declined
    EXPIRED = 4      # donation.expired


@dataclass
class Donation:
    """
    Donation entity representing a donation in the system
    
    This is a core business entity that contains the essential
    attributes and business rules for donations. Based on the real
    database schema from schema.sql.
    """
    id: Optional[UUID]
    amount_gtq: Decimal
    status_id: int
    donor_email: str
    donor_name: Optional[str]
    donor_nit: Optional[str]
    user_id: Optional[UUID]
    payu_order_id: Optional[str]
    reference_code: str
    correlation_id: str
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime]
    
    def __post_init__(self):
        """Validation after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate donation business rules"""
        if self.amount_gtq <= 0:
            raise ValueError("Donation amount must be positive")
        
        if not self.donor_email.strip():
            raise ValueError("Donor email cannot be empty")
        
        if "@" not in self.donor_email:
            raise ValueError("Invalid email format")
        
        if not self.reference_code.strip():
            raise ValueError("Reference code cannot be empty")
        
        if not self.correlation_id.strip():
            raise ValueError("Correlation ID cannot be empty")
        
        if self.status_id not in [status.value for status in DonationStatus]:
            raise ValueError(f"Invalid status_id: {self.status_id}")
    
    def approve(self) -> None:
        """Mark donation as approved"""
        if self.status_id != DonationStatus.PENDING.value:
            raise ValueError("Only pending donations can be approved")
        
        self.status_id = DonationStatus.APPROVED.value
        self.paid_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def decline(self) -> None:
        """Decline the donation"""
        if self.status_id in [DonationStatus.APPROVED.value]:
            raise ValueError("Cannot decline approved donations")
        
        self.status_id = DonationStatus.DECLINED.value
        self.updated_at = datetime.utcnow()
    
    def expire(self) -> None:
        """Mark donation as expired"""
        if self.status_id != DonationStatus.PENDING.value:
            raise ValueError("Only pending donations can be expired")
        
        self.status_id = DonationStatus.EXPIRED.value
        self.updated_at = datetime.utcnow()
    
    @property
    def status(self) -> DonationStatus:
        """Get donation status enum"""
        return DonationStatus(self.status_id)
    
    @property
    def is_approved(self) -> bool:
        """Check if donation is approved"""
        return self.status_id == DonationStatus.APPROVED.value
    
    @property
    def is_pending(self) -> bool:
        """Check if donation is pending"""
        return self.status_id == DonationStatus.PENDING.value
    
    @property
    def is_declined(self) -> bool:
        """Check if donation is declined"""
        return self.status_id == DonationStatus.DECLINED.value
    
    @property
    def is_expired(self) -> bool:
        """Check if donation is expired"""
        return self.status_id == DonationStatus.EXPIRED.value
    
    @property
    def formatted_amount(self) -> str:
        """Get formatted amount with GTQ currency"""
        return f"Q{self.amount_gtq:.2f}"