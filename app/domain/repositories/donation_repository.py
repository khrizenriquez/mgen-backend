"""
Donation Repository Interface - Port for data access
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID

from app.domain.entities.donation import Donation, DonationStatus


class DonationRepository(ABC):
    """
    Abstract repository interface for donation data access
    
    This defines the contract that infrastructure implementations
    must follow (Dependency Inversion Principle)
    """
    
    @abstractmethod
    async def create(self, donation: Donation) -> Donation:
        """Create a new donation"""
        pass
    
    @abstractmethod
    async def get_by_id(self, donation_id: UUID) -> Optional[Donation]:
        """Get donation by ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> List[Donation]:
        """Get all donations by donor email"""
        pass
    
    @abstractmethod
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[DonationStatus] = None,
        organization_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> List[Donation]:
        """Get all donations with optional filtering"""
        pass
    
    @abstractmethod
    async def update(self, donation: Donation) -> Donation:
        """Update an existing donation"""
        pass
    
    @abstractmethod
    async def delete(self, donation_id: UUID) -> bool:
        """Delete a donation"""
        pass
    
    @abstractmethod
    async def get_total_amount_by_status(self, status: DonationStatus) -> Decimal:
        """Get total amount for donations with specific status"""
        pass
    
    @abstractmethod
    async def get_donations_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Donation]:
        """Get donations within date range"""
        pass
    
    @abstractmethod
    async def count_by_status(self, status: DonationStatus) -> int:
        """Count donations by status"""
        pass