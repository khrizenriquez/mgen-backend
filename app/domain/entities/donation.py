"""
Donation Entity - Core business model
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass
from decimal import Decimal


class DonationStatus(Enum):
    """Donation status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DonationType(Enum):
    """Donation type enumeration"""
    MONETARY = "monetary"
    GOODS = "goods"
    SERVICES = "services"


@dataclass
class Donation:
    """
    Donation entity representing a donation in the system
    
    This is a core business entity that contains the essential
    attributes and business rules for donations.
    """
    id: Optional[int]
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
    
    def __post_init__(self):
        """Validation after initialization"""
        self.validate()
    
    def validate(self) -> None:
        """Validate donation business rules"""
        if self.amount <= 0:
            raise ValueError("Donation amount must be positive")
        
        if not self.donor_name.strip():
            raise ValueError("Donor name cannot be empty")
        
        if not self.donor_email.strip():
            raise ValueError("Donor email cannot be empty")
        
        if "@" not in self.donor_email:
            raise ValueError("Invalid email format")
    
    def complete(self) -> None:
        """Mark donation as completed"""
        if self.status != DonationStatus.PENDING:
            raise ValueError("Only pending donations can be completed")
        
        self.status = DonationStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """Cancel the donation"""
        if self.status in [DonationStatus.COMPLETED, DonationStatus.FAILED]:
            raise ValueError("Cannot cancel completed or failed donations")
        
        self.status = DonationStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def fail(self, reason: Optional[str] = None) -> None:
        """Mark donation as failed"""
        if self.status != DonationStatus.PENDING:
            raise ValueError("Only pending donations can be marked as failed")
        
        self.status = DonationStatus.FAILED
        self.updated_at = datetime.utcnow()
        
        if reason:
            self.description = f"{self.description or ''} - Failed: {reason}"
    
    @property
    def is_completed(self) -> bool:
        """Check if donation is completed"""
        return self.status == DonationStatus.COMPLETED
    
    @property
    def is_pending(self) -> bool:
        """Check if donation is pending"""
        return self.status == DonationStatus.PENDING
    
    @property
    def formatted_amount(self) -> str:
        """Get formatted amount with currency"""
        return f"{self.amount:.2f} {self.currency}"