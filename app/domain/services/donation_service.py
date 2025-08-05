"""
Donation Service - Business Logic and Use Cases
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import logging

from app.domain.entities.donation import Donation, DonationStatus, DonationType
from app.domain.repositories.donation_repository import DonationRepository


logger = logging.getLogger(__name__)


class DonationService:
    """
    Domain service containing business logic for donations
    
    This service orchestrates business operations and enforces
    business rules across multiple entities
    """
    
    def __init__(self, donation_repository: DonationRepository):
        self.donation_repository = donation_repository
    
    async def create_donation(
        self,
        donor_name: str,
        donor_email: str,
        amount: Decimal,
        currency: str,
        donation_type: DonationType,
        description: Optional[str] = None
    ) -> Donation:
        """
        Create a new donation with business validation
        """
        logger.info(f"Creating donation for {donor_email}, amount: {amount} {currency}")
        
        # Business rule: Minimum donation amount
        min_amount = Decimal("1.00")
        if amount < min_amount:
            raise ValueError(f"Minimum donation amount is {min_amount} {currency}")
        
        # Business rule: Maximum donation amount for single transaction
        max_amount = Decimal("10000.00")
        if amount > max_amount:
            raise ValueError(f"Maximum donation amount is {max_amount} {currency}")
        
        # Create donation entity
        now = datetime.utcnow()
        donation = Donation(
            id=None,
            donor_name=donor_name.strip(),
            donor_email=donor_email.strip().lower(),
            amount=amount,
            currency=currency.upper(),
            donation_type=donation_type,
            status=DonationStatus.PENDING,
            description=description,
            created_at=now,
            updated_at=now,
            completed_at=None
        )
        
        # Save donation
        created_donation = await self.donation_repository.create(donation)
        
        logger.info(f"Donation created with ID: {created_donation.id}")
        return created_donation
    
    async def process_donation(self, donation_id: int) -> Donation:
        """
        Process a pending donation
        """
        logger.info(f"Processing donation {donation_id}")
        
        donation = await self.donation_repository.get_by_id(donation_id)
        if not donation:
            raise ValueError(f"Donation with ID {donation_id} not found")
        
        if not donation.is_pending:
            raise ValueError(f"Donation {donation_id} is not in pending status")
        
        try:
            # Here you would integrate with payment processor
            # For now, we'll just mark as completed
            donation.complete()
            
            updated_donation = await self.donation_repository.update(donation)
            logger.info(f"Donation {donation_id} processed successfully")
            
            return updated_donation
            
        except Exception as e:
            logger.error(f"Failed to process donation {donation_id}: {e}")
            donation.fail(str(e))
            await self.donation_repository.update(donation)
            raise
    
    async def cancel_donation(self, donation_id: int) -> Donation:
        """
        Cancel a donation
        """
        logger.info(f"Cancelling donation {donation_id}")
        
        donation = await self.donation_repository.get_by_id(donation_id)
        if not donation:
            raise ValueError(f"Donation with ID {donation_id} not found")
        
        donation.cancel()
        updated_donation = await self.donation_repository.update(donation)
        
        logger.info(f"Donation {donation_id} cancelled")
        return updated_donation
    
    async def get_donation_statistics(self) -> dict:
        """
        Get donation statistics
        """
        total_completed = await self.donation_repository.get_total_amount_by_status(
            DonationStatus.COMPLETED
        )
        total_pending = await self.donation_repository.get_total_amount_by_status(
            DonationStatus.PENDING
        )
        
        count_completed = await self.donation_repository.count_by_status(
            DonationStatus.COMPLETED
        )
        count_pending = await self.donation_repository.count_by_status(
            DonationStatus.PENDING
        )
        count_failed = await self.donation_repository.count_by_status(
            DonationStatus.FAILED
        )
        
        return {
            "total_amount_completed": float(total_completed),
            "total_amount_pending": float(total_pending),
            "count_completed": count_completed,
            "count_pending": count_pending,
            "count_failed": count_failed,
            "success_rate": count_completed / max(count_completed + count_failed, 1) * 100
        }
    
    async def get_donor_donations(self, email: str) -> List[Donation]:
        """
        Get all donations for a specific donor
        """
        return await self.donation_repository.get_by_email(email.strip().lower())