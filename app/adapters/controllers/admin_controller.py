"""
Admin controller with administrative endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.adapters.schemas.user_schemas import UserResponse, UserListResponse
from app.adapters.schemas.donation_schemas import DonationResponse, DonationListResponse, DonationStatusUpdate
from app.adapters.schemas.auth_schemas import GenericResponse
from app.domain.services.user_service import UserService
from app.domain.services.donation_service import DonationService
from app.infrastructure.database.user_repository_impl import UserRepositoryImpl
from app.infrastructure.database.donation_repository_impl import DonationRepositoryImpl
from app.infrastructure.database.database import get_db
from app.infrastructure.auth.dependencies import require_admin
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency to get user service"""
    user_repository = UserRepositoryImpl(db)
    return UserService(user_repository)


def get_donation_service(db: Session = Depends(get_db)) -> DonationService:
    """Dependency to get donation service"""
    donation_repository = DonationRepositoryImpl(db)
    return DonationService(donation_repository)


# User management endpoints
@router.post("/users", response_model=UserResponse)
async def create_admin_user(
    user_data: dict,  # Simplified - would use UserCreate schema
    current_user = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Create a new user (Admin only)

    Creates a new user in the system with the specified details.
    """
    from app.domain.entities.user import User

    user = User(
        email=user_data.get("email"),
        first_name=user_data.get("first_name", ""),
        last_name=user_data.get("last_name", ""),
        is_active=user_data.get("is_active", True)
    )

    created_user = await user_service.create_user(user)
    return UserResponse(
        id=created_user.id,
        email=created_user.email,
        first_name=created_user.first_name,
        last_name=created_user.last_name,
        is_active=created_user.is_active,
        created_at=created_user.created_at,
        updated_at=created_user.updated_at
    )


@router.get("/users", response_model=UserListResponse)
async def get_admin_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    current_user = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get all users with admin controls (Admin only)

    Returns a paginated list of all users in the system with admin controls.
    """
    users = await user_service.get_users(skip=skip, limit=limit)

    # Convert to UserResponse format
    user_responses = []
    for user in users:
        user_responses.append(UserResponse(
            id=user.id,
            email=user.email,
            first_name=getattr(user, 'first_name', ''),
            last_name=getattr(user, 'last_name', ''),
            is_active=getattr(user, 'is_active', True),
            created_at=getattr(user, 'created_at', None),
            updated_at=getattr(user, 'updated_at', None)
        ))

    return UserListResponse(
        users=user_responses,
        total=len(user_responses),  # This should come from the service
        skip=skip,
        limit=limit
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_admin_user(
    user_id: int,
    user_data: dict,  # Simplified - would use UserUpdate schema
    current_user = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user by ID (Admin only)

    Updates user information including role assignments and status.
    """
    from app.domain.entities.user import User

    user = User(
        email=user_data.get("email"),
        first_name=user_data.get("first_name", ""),
        last_name=user_data.get("last_name", ""),
        is_active=user_data.get("is_active", True)
    )

    updated_user = await user_service.update_user(user_id, user)
    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at
    )


@router.delete("/users/{user_id}", response_model=GenericResponse)
async def delete_admin_user(
    user_id: int,
    current_user = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete user by ID (Admin only)

    Permanently removes a user from the system.
    """
    # Prevent admin from deleting themselves
    if str(current_user.id) == str(user_id):
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own admin account"
        )

    await user_service.delete_user(user_id)
    return GenericResponse(message="User deleted successfully")


# Donation management endpoints
@router.get("/donations", response_model=DonationListResponse)
async def get_admin_donations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    status_filter: str = Query(None, description="Filter by donation status"),
    current_user = Depends(require_admin),
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Get all donations with admin controls (Admin only)

    Returns a paginated list of all donations with admin management capabilities.
    """
    donations = await donation_service.get_donations(
        skip=skip,
        limit=limit,
        status_filter=status_filter
    )

    # Convert to DonationResponse format
    donation_responses = []
    for donation in donations:
        donation_responses.append(DonationResponse(
            id=donation.id,
            amount_gtq=donation.amount_gtq,
            status_name=getattr(donation, 'status_name', 'Unknown'),
            donor_email=getattr(donation, 'donor_email', ''),
            donor_name=getattr(donation, 'donor_name', ''),
            reference_code=getattr(donation, 'reference_code', ''),
            created_at=getattr(donation, 'created_at', None),
            paid_at=getattr(donation, 'paid_at', None)
        ))

    return DonationListResponse(
        donations=donation_responses,
        total=len(donation_responses),  # This should come from the service
        skip=skip,
        limit=limit
    )


@router.put("/donations/{donation_id}/status", response_model=GenericResponse)
async def update_donation_status(
    donation_id: int,
    status_data: DonationStatusUpdate,
    current_user = Depends(require_admin),
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Update donation status (Admin only)

    Allows admins to approve, reject, or change the status of donations.
    """
    success = await donation_service.update_donation_status(donation_id, status_data.status_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Donation not found"
        )

    return GenericResponse(message=f"Donation status updated to {status_data.status_id}")


@router.get("/donations/{donation_id}", response_model=DonationResponse)
async def get_admin_donation_detail(
    donation_id: int,
    current_user = Depends(require_admin),
    donation_service: DonationService = Depends(get_donation_service)
):
    """
    Get detailed donation information (Admin only)

    Returns complete donation details including payment information and history.
    """
    donation = await donation_service.get_donation_by_id(donation_id)
    if not donation:
        raise HTTPException(
            status_code=404,
            detail="Donation not found"
        )

    return DonationResponse(
        id=donation.id,
        amount_gtq=donation.amount_gtq,
        status_name=getattr(donation, 'status_name', 'Unknown'),
        donor_email=getattr(donation, 'donor_email', ''),
        donor_name=getattr(donation, 'donor_name', ''),
        reference_code=getattr(donation, 'reference_code', ''),
        created_at=getattr(donation, 'created_at', None),
        paid_at=getattr(donation, 'paid_at', None)
    )
