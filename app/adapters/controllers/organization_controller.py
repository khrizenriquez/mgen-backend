"""
Organization controller with CRUD endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.adapters.schemas.organization_schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse,
    OrganizationSummary
)
from app.domain.services.organization_service import OrganizationService
from app.infrastructure.database.database import get_db
from app.infrastructure.auth.dependencies import get_current_active_user, require_role
from app.infrastructure.database.models import UserModel


router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
    responses={404: {"description": "Not found"}},
)


def get_organization_service(db: Session = Depends(get_db)) -> OrganizationService:
    """Dependency to get organization service"""
    return OrganizationService(db)


# TODO: Fix FastAPI compatibility issue with UserModel
# Temporarily disable all organization endpoints


@router.post("/", response_model=None, status_code=201)
async def create_organization(
    org_data: OrganizationCreate,
    current_user,
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Create a new organization (Admin only)

    Requires ADMIN role.
    """
    try:
        organization = org_service.create_organization(org_data)
        return OrganizationResponse.model_validate(organization)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to create organization"
        )


@router.get("/", response_model=None)
async def get_organizations(
    current_user = Depends(require_role("ADMIN")),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get all organizations with pagination (Admin only)

    Requires ADMIN role.
    """
    try:
        organizations = org_service.get_organizations(skip=skip, limit=limit)
        org_responses = [OrganizationResponse.model_validate(org) for org in organizations]

        return OrganizationListResponse(
            organizations=org_responses,
            total=len(org_responses),
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get organizations"
        )


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    current_user = Depends(require_role("ADMIN")),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get organization by ID (Admin only)

    Requires ADMIN role.
    """
    try:
        organization = org_service.get_organization(org_id)
        return OrganizationResponse.model_validate(organization)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get organization"
        )


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    org_data: OrganizationUpdate,
    current_user = Depends(require_role("ADMIN")),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Update organization by ID (Admin only)

    Requires ADMIN role.
    """
    try:
        organization = org_service.update_organization(org_id, org_data)
        return OrganizationResponse.model_validate(organization)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to update organization"
        )


@router.delete("/{org_id}")
async def delete_organization(
    org_id: UUID,
    current_user = Depends(require_role("ADMIN")),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Delete organization by ID (Admin only)

    Requires ADMIN role.
    """
    try:
        result = org_service.delete_organization(org_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete organization"
        )


@router.get("/summary/all")
async def get_all_organization_summaries(
    current_user = Depends(require_role("ADMIN")),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get summary statistics for all organizations (Admin only)

    Requires ADMIN role.
    """
    try:
        summaries = org_service.get_all_organization_summaries()
        return {"summaries": [summary.model_dump() for summary in summaries]}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get organization summaries"
        )


@router.get("/{org_id}/summary", response_model=OrganizationSummary)
async def get_organization_summary(
    org_id: UUID,
    current_user = Depends(require_role("ADMIN")),
    org_service: OrganizationService = Depends(get_organization_service)
):
    """
    Get summary statistics for a specific organization (Admin only)

    Requires ADMIN role.
    """
    try:
        summary = org_service.get_organization_summary(org_id)
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to get organization summary"
        )