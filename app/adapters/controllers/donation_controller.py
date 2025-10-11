"""
Donation Controller - HTTP API endpoints (Simplified version)
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
import logging
from decimal import Decimal

from app.domain.entities.donation import DonationStatus
from app.infrastructure.database.repository_impl import SQLAlchemyDonationRepository
from app.infrastructure.database.database import get_db
from app.infrastructure.logging import get_logger
from app.infrastructure.auth.dependencies import (
    get_current_active_user, require_admin, require_organization, require_auditor, require_any_role
)
from app.infrastructure.database.models import UserModel
from app.adapters.schemas.donation_schemas import (
    DonationCreateRequest, DonationResponse, DonationUpdateRequest
)

logger = get_logger(__name__)
router = APIRouter()


def get_donation_repository(db=Depends(get_db)) -> SQLAlchemyDonationRepository:
    """Dependency injection for donation repository"""
    return SQLAlchemyDonationRepository(db)


@router.get("/donations")
async def list_donations(
    current_user: UserModel = Depends(get_current_active_user),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[DonationStatus] = None,
    repository: SQLAlchemyDonationRepository = Depends(get_donation_repository)
):
    """List donations with optional filtering

    Requires authentication:
    - ADMIN: See all donations in the system
    - ORGANIZATION: See donations from their organization (TODO: implement organization filtering)
    - AUDITOR: See all donations (read-only access)
    - DONOR: See only their own donations
    - USER: No access (empty list)
    """
    try:
        logger.info(
            "Fetching donations list",
            user_email=current_user.email,
            limit=limit,
            offset=offset,
            status=status.name if status else None
        )

        # Check user roles
        user_roles = [role.name for role in current_user.user_roles]
        is_admin = "ADMIN" in user_roles
        is_organization = "ORGANIZATION" in user_roles
        is_auditor = "AUDITOR" in user_roles
        is_donor = "DONOR" in user_roles

        # Filter donations based on role
        if is_admin:
            # Admins see all donations
            donations = await repository.get_all(
                limit=limit,
                offset=offset,
                status=status
            )
        elif is_organization:
            # Organizations see donations from their organization (TODO: implement organization filtering)
            # For now, same as admin
            donations = await repository.get_all(
                limit=limit,
                offset=offset,
                status=status
            )
        elif is_auditor:
            # Auditors see all donations (read-only)
            donations = await repository.get_all(
                limit=limit,
                offset=offset,
                status=status
            )
        elif is_donor:
            # Donors see only their own donations
            donations = await repository.get_all(
                limit=limit,
                offset=offset,
                status=status,
                user_id=current_user.id
            )
        else:
            # Other users see no donations
            donations = []
        
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
    current_user: UserModel = Depends(get_current_active_user),
    repository: SQLAlchemyDonationRepository = Depends(get_donation_repository)
):
    """Get donation statistics

    Requires authentication:
    - ADMIN: See global statistics
    - ORGANIZATION: See statistics from their organization (TODO: implement organization filtering)
    - AUDITOR: See global statistics (read-only)
    - DONOR: See statistics from their own donations
    - USER: No access (zero statistics)
    """
    try:
        logger.info("Fetching donation statistics", user_email=current_user.email)

        # Check user roles
        user_roles = [role.name for role in current_user.user_roles]
        is_admin = "ADMIN" in user_roles
        is_organization = "ORGANIZATION" in user_roles
        is_auditor = "AUDITOR" in user_roles
        is_donor = "DONOR" in user_roles

        if is_admin:
            # Admins see global statistics
            pending_total = await repository.get_total_amount_by_status(DonationStatus.PENDING)
            approved_total = await repository.get_total_amount_by_status(DonationStatus.APPROVED)
            declined_total = await repository.get_total_amount_by_status(DonationStatus.DECLINED)
            expired_total = await repository.get_total_amount_by_status(DonationStatus.EXPIRED)

            pending_count = await repository.count_by_status(DonationStatus.PENDING)
            approved_count = await repository.count_by_status(DonationStatus.APPROVED)
            declined_count = await repository.count_by_status(DonationStatus.DECLINED)
            expired_count = await repository.count_by_status(DonationStatus.EXPIRED)
        elif is_organization:
            # Organizations see statistics from their organization (TODO: implement organization filtering)
            # For now, same as admin
            pending_total = await repository.get_total_amount_by_status(DonationStatus.PENDING)
            approved_total = await repository.get_total_amount_by_status(DonationStatus.APPROVED)
            declined_total = await repository.get_total_amount_by_status(DonationStatus.DECLINED)
            expired_total = await repository.get_total_amount_by_status(DonationStatus.EXPIRED)

            pending_count = await repository.count_by_status(DonationStatus.PENDING)
            approved_count = await repository.count_by_status(DonationStatus.APPROVED)
            declined_count = await repository.count_by_status(DonationStatus.DECLINED)
            expired_count = await repository.count_by_status(DonationStatus.EXPIRED)
        elif is_auditor:
            # Auditors see global statistics (read-only)
            pending_total = await repository.get_total_amount_by_status(DonationStatus.PENDING)
            approved_total = await repository.get_total_amount_by_status(DonationStatus.APPROVED)
            declined_total = await repository.get_total_amount_by_status(DonationStatus.DECLINED)
            expired_total = await repository.get_total_amount_by_status(DonationStatus.EXPIRED)

            pending_count = await repository.count_by_status(DonationStatus.PENDING)
            approved_count = await repository.count_by_status(DonationStatus.APPROVED)
            declined_count = await repository.count_by_status(DonationStatus.DECLINED)
            expired_count = await repository.count_by_status(DonationStatus.EXPIRED)
        elif is_donor:
            # Donors see only their own donation statistics
            pending_total = await repository.get_total_amount_by_status(DonationStatus.PENDING, user_id=current_user.id)
            approved_total = await repository.get_total_amount_by_status(DonationStatus.APPROVED, user_id=current_user.id)
            declined_total = await repository.get_total_amount_by_status(DonationStatus.DECLINED, user_id=current_user.id)
            expired_total = await repository.get_total_amount_by_status(DonationStatus.EXPIRED, user_id=current_user.id)

            pending_count = await repository.count_by_status(DonationStatus.PENDING, user_id=current_user.id)
            approved_count = await repository.count_by_status(DonationStatus.APPROVED, user_id=current_user.id)
            declined_count = await repository.count_by_status(DonationStatus.DECLINED, user_id=current_user.id)
            expired_count = await repository.count_by_status(DonationStatus.EXPIRED, user_id=current_user.id)
        else:
            # Other users see no statistics
            pending_total = approved_total = declined_total = expired_total = 0
            pending_count = approved_count = declined_count = expired_count = 0
        
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


@router.post("/donations", response_model=None)
async def create_donation(
    donation_data: DonationCreateRequest,
    current_user = Depends(get_current_active_user),
    repository: SQLAlchemyDonationRepository = Depends(get_donation_repository)
):
    """Create a new donation

    Requires authentication. Anyone can create a donation.
    """
    try:
        logger.info(
            "Creating donation",
            user_email=current_user.email,
            donor_email=donation_data.donor_email,
            amount=donation_data.amount
        )

        # For now, we'll create a basic donation record
        # In a real implementation, this would integrate with payment processing
        from app.domain.entities.donation import Donation, DonationType
        from datetime import datetime

        now = datetime.utcnow()
        donation = Donation(
            id=None,
            amount_gtq=donation_data.amount,
            status_id=1,  # PENDING
            donor_email=donation_data.donor_email,
            donor_name=donation_data.donor_name,
            donor_nit=None,
            user_id=current_user.id if hasattr(current_user, 'id') else None,
            payu_order_id=None,
            reference_code=f"REF-{now.strftime('%Y%m%d%H%M%S')}",
            correlation_id=f"CORR-{now.strftime('%Y%m%d%H%M%S')}",
            created_at=now,
            updated_at=now,
            paid_at=None
        )

        created_donation = await repository.create(donation)

        logger.info(
            "Donation created successfully",
            donation_id=str(created_donation.id),
            reference_code=created_donation.reference_code
        )

        return {
            "id": str(created_donation.id),
            "amount_gtq": float(created_donation.amount_gtq),
            "status_id": created_donation.status_id,
            "donor_email": created_donation.donor_email,
            "donor_name": created_donation.donor_name,
            "reference_code": created_donation.reference_code,
            "correlation_id": created_donation.correlation_id,
            "created_at": created_donation.created_at.isoformat(),
            "updated_at": created_donation.updated_at.isoformat()
        }

    except Exception as e:
        logger.error(
            "Error creating donation",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/donations/{donation_id}")
async def get_donation(
    donation_id: str,
    current_user = Depends(get_current_active_user),
    repository: SQLAlchemyDonationRepository = Depends(get_donation_repository)
):
    """Get a specific donation by ID

    Requires authentication. Users can only view their own donations unless they are admin/organization/auditor.
    """
    try:
        from uuid import UUID
        donation_uuid = UUID(donation_id)

        logger.info(
            "Fetching donation by ID",
            user_email=current_user.email,
            donation_id=donation_id
        )

        donation = await repository.get_by_id(donation_uuid)
        if not donation:
            raise HTTPException(status_code=404, detail="Donation not found")

        # Check permissions
        user_roles = [role.name for role in current_user.user_roles]
        is_admin = "ADMIN" in user_roles
        is_organization = "ORGANIZATION" in user_roles
        is_auditor = "AUDITOR" in user_roles

        # Users can only see their own donations unless they have elevated roles
        if not (is_admin or is_organization or is_auditor):
            if donation.user_id != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You can only access your own donations"
                )

        logger.info(
            "Donation retrieved successfully",
            donation_id=donation_id
        )

        return {
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
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting donation",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/donations/{donation_id}")
async def update_donation(
    donation_id: str,
    donation_data: DonationUpdateRequest,
    current_user = Depends(require_admin),  # Only admins can update donations
    repository: SQLAlchemyDonationRepository = Depends(get_donation_repository)
):
    """Update a donation

    Requires ADMIN role.
    """
    try:
        from uuid import UUID
        donation_uuid = UUID(donation_id)

        logger.info(
            "Updating donation",
            user_email=current_user.email,
            donation_id=donation_id
        )

        donation = await repository.get_by_id(donation_uuid)
        if not donation:
            raise HTTPException(status_code=404, detail="Donation not found")

        # Update fields if provided
        if donation_data.description is not None:
            # Note: The current model doesn't have description field
            # This would need to be added to the model if needed
            pass

        # For now, we'll just update the updated_at timestamp
        from datetime import datetime
        donation.updated_at = datetime.utcnow()

        updated_donation = await repository.update(donation)

        logger.info(
            "Donation updated successfully",
            donation_id=donation_id
        )

        return {
            "id": str(updated_donation.id),
            "amount_gtq": float(updated_donation.amount_gtq),
            "status_id": updated_donation.status_id,
            "status_name": updated_donation.status.name,
            "donor_email": updated_donation.donor_email,
            "donor_name": updated_donation.donor_name,
            "donor_nit": updated_donation.donor_nit,
            "reference_code": updated_donation.reference_code,
            "correlation_id": updated_donation.correlation_id,
            "created_at": updated_donation.created_at.isoformat(),
            "updated_at": updated_donation.updated_at.isoformat(),
            "paid_at": updated_donation.paid_at.isoformat() if updated_donation.paid_at else None,
            "formatted_amount": updated_donation.formatted_amount
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating donation",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/donations/{donation_id}")
async def delete_donation(
    donation_id: str,
    current_user = Depends(require_admin),  # Only admins can delete donations
    repository: SQLAlchemyDonationRepository = Depends(get_donation_repository)
):
    """Delete a donation

    Requires ADMIN role.
    """
    try:
        from uuid import UUID
        donation_uuid = UUID(donation_id)

        logger.info(
            "Deleting donation",
            user_email=current_user.email,
            donation_id=donation_id
        )

        deleted = await repository.delete(donation_uuid)
        if not deleted:
            raise HTTPException(status_code=404, detail="Donation not found")

        logger.info(
            "Donation deleted successfully",
            donation_id=donation_id
        )

        return {"message": "Donation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting donation",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")