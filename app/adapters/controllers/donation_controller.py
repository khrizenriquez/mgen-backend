"""
Donation Controller - HTTP API endpoints (Simplified version)
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging
from decimal import Decimal

from app.domain.entities.donation import DonationStatus
from app.infrastructure.database.repository_impl import SQLAlchemyDonationRepository
from app.infrastructure.database.database import get_db
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_donation_repository(db=Depends(get_db)) -> SQLAlchemyDonationRepository:
    """Dependency injection for donation repository"""
    return SQLAlchemyDonationRepository(db)


@router.get("/donations")
async def list_donations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[DonationStatus] = None,
    repository: SQLAlchemyDonationRepository = Depends(get_donation_repository)
):
    """List donations with optional filtering (simplified version)"""
    try:
        logger.info(
            "Fetching donations list",
            limit=limit,
            offset=offset,
            status=status.name if status else None
        )
        
        donations = await repository.get_all(
            limit=limit,
            offset=offset,
            status=status
        )
        
        donation_responses = []
        for donation in donations:
            donation_responses.append({
                "id": str(donation.id),
                "amount_gtq": float(donation.amount_gtq),
                "status_id": donation.status_id,
                "status_name": donation.status.name,
                "donor_email": donation.donor_email,
                "donor_name": donation.donor_name,
                "donor_nit": donation.donor_nit,
                "reference_code": donation.reference_code,
                "correlation_id": donation.correlation_id,
                "created_at": donation.created_at.isoformat(),
                "updated_at": donation.updated_at.isoformat(),
                "paid_at": donation.paid_at.isoformat() if donation.paid_at else None,
                "formatted_amount": donation.formatted_amount
            })
        
        logger.info(
            "Successfully fetched donations",
            count=len(donation_responses),
            limit=limit,
            offset=offset
        )
        
        return {
            "donations": donation_responses,
            "total": len(donation_responses),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(
            "Error listing donations",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/donations/stats")
async def get_donation_statistics(
    repository: SQLAlchemyDonationRepository = Depends(get_donation_repository)
):
    """Get donation statistics (simplified version)"""
    try:
        logger.info("Fetching donation statistics")
        
        # Get total amounts by status
        pending_total = await repository.get_total_amount_by_status(DonationStatus.PENDING)
        approved_total = await repository.get_total_amount_by_status(DonationStatus.APPROVED)
        declined_total = await repository.get_total_amount_by_status(DonationStatus.DECLINED)
        expired_total = await repository.get_total_amount_by_status(DonationStatus.EXPIRED)
        
        # Get counts by status
        pending_count = await repository.count_by_status(DonationStatus.PENDING)
        approved_count = await repository.count_by_status(DonationStatus.APPROVED)
        declined_count = await repository.count_by_status(DonationStatus.DECLINED)
        expired_count = await repository.count_by_status(DonationStatus.EXPIRED)
        
        stats = {
            "total_amount_gtq": float(pending_total + approved_total + declined_total + expired_total),
            "total_donations": pending_count + approved_count + declined_count + expired_count,
            "by_status": {
                "pending": {
                    "count": pending_count,
                    "amount_gtq": float(pending_total)
                },
                "approved": {
                    "count": approved_count,
                    "amount_gtq": float(approved_total)
                },
                "declined": {
                    "count": declined_count,
                    "amount_gtq": float(declined_total)
                },
                "expired": {
                    "count": expired_count,
                    "amount_gtq": float(expired_total)
                }
            }
        }
        
        logger.info(
            "Successfully fetched donation statistics",
            total_donations=stats["total_donations"],
            total_amount=stats["total_amount_gtq"]
        )
        
        return stats
        
    except Exception as e:
        logger.error(
            "Error getting donation statistics",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")