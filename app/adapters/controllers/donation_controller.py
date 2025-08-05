"""
Donation Controller - HTTP API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from app.domain.entities.donation import DonationStatus, DonationType
from app.domain.services.donation_service import DonationService
from app.adapters.schemas.donation_schemas import (
    DonationCreateRequest,
    DonationResponse,
    DonationUpdateRequest,
    DonationListResponse,
    DonationStatsResponse
)
from app.infrastructure.database.repository_impl import SQLAlchemyDonationRepository
from app.infrastructure.database.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


def get_donation_service(db=Depends(get_db)) -> DonationService:
    """Dependency injection for donation service"""
    repository = SQLAlchemyDonationRepository(db)
    return DonationService(repository)


@router.post("/donations", response_model=DonationResponse, status_code=201)
async def create_donation(
    request: DonationCreateRequest,
    service: DonationService = Depends(get_donation_service)
):
    """Create a new donation"""
    try:
        donation = await service.create_donation(
            donor_name=request.donor_name,
            donor_email=request.donor_email,
            amount=request.amount,
            currency=request.currency,
            donation_type=request.donation_type,
            description=request.description
        )
        
        return DonationResponse(
            id=donation.id,
            donor_name=donation.donor_name,
            donor_email=donation.donor_email,
            amount=donation.amount,
            currency=donation.currency,
            donation_type=donation.donation_type,
            status=donation.status,
            description=donation.description,
            created_at=donation.created_at,
            updated_at=donation.updated_at,
            completed_at=donation.completed_at,
            formatted_amount=donation.formatted_amount
        )
        
    except ValueError as e:
        logger.error(f"Validation error creating donation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating donation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/donations/{donation_id}", response_model=DonationResponse)
async def get_donation(
    donation_id: int,
    service: DonationService = Depends(get_donation_service)
):
    """Get donation by ID"""
    try:
        donation = await service.donation_repository.get_by_id(donation_id)
        if not donation:
            raise HTTPException(status_code=404, detail="Donation not found")
        
        return DonationResponse(
            id=donation.id,
            donor_name=donation.donor_name,
            donor_email=donation.donor_email,
            amount=donation.amount,
            currency=donation.currency,
            donation_type=donation.donation_type,
            status=donation.status,
            description=donation.description,
            created_at=donation.created_at,
            updated_at=donation.updated_at,
            completed_at=donation.completed_at,
            formatted_amount=donation.formatted_amount
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting donation {donation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/donations", response_model=DonationListResponse)
async def list_donations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[DonationStatus] = None,
    donation_type: Optional[DonationType] = None,
    service: DonationService = Depends(get_donation_service)
):
    """List donations with optional filtering"""
    try:
        donations = await service.donation_repository.get_all(
            limit=limit,
            offset=offset,
            status=status,
            donation_type=donation_type
        )
        
        donation_responses = [
            DonationResponse(
                id=donation.id,
                donor_name=donation.donor_name,
                donor_email=donation.donor_email,
                amount=donation.amount,
                currency=donation.currency,
                donation_type=donation.donation_type,
                status=donation.status,
                description=donation.description,
                created_at=donation.created_at,
                updated_at=donation.updated_at,
                completed_at=donation.completed_at,
                formatted_amount=donation.formatted_amount
            )
            for donation in donations
        ]
        
        return DonationListResponse(
            donations=donation_responses,
            total=len(donation_responses),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Error listing donations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/donations/{donation_id}/process", response_model=DonationResponse)
async def process_donation(
    donation_id: int,
    service: DonationService = Depends(get_donation_service)
):
    """Process a pending donation"""
    try:
        donation = await service.process_donation(donation_id)
        
        return DonationResponse(
            id=donation.id,
            donor_name=donation.donor_name,
            donor_email=donation.donor_email,
            amount=donation.amount,
            currency=donation.currency,
            donation_type=donation.donation_type,
            status=donation.status,
            description=donation.description,
            created_at=donation.created_at,
            updated_at=donation.updated_at,
            completed_at=donation.completed_at,
            formatted_amount=donation.formatted_amount
        )
        
    except ValueError as e:
        logger.error(f"Validation error processing donation {donation_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing donation {donation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/donations/{donation_id}/cancel", response_model=DonationResponse)
async def cancel_donation(
    donation_id: int,
    service: DonationService = Depends(get_donation_service)
):
    """Cancel a donation"""
    try:
        donation = await service.cancel_donation(donation_id)
        
        return DonationResponse(
            id=donation.id,
            donor_name=donation.donor_name,
            donor_email=donation.donor_email,
            amount=donation.amount,
            currency=donation.currency,
            donation_type=donation.donation_type,
            status=donation.status,
            description=donation.description,
            created_at=donation.created_at,
            updated_at=donation.updated_at,
            completed_at=donation.completed_at,
            formatted_amount=donation.formatted_amount
        )
        
    except ValueError as e:
        logger.error(f"Validation error cancelling donation {donation_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling donation {donation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/donations/stats", response_model=DonationStatsResponse)
async def get_donation_statistics(
    service: DonationService = Depends(get_donation_service)
):
    """Get donation statistics"""
    try:
        stats = await service.get_donation_statistics()
        return DonationStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting donation statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")