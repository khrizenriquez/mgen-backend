"""
Organization service with business logic
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.adapters.schemas.organization_schemas import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse, OrganizationSummary
)
from app.infrastructure.database.models import OrganizationModel, UserModel, DonationModel


class OrganizationService:
    """Organization service with business logic"""

    def __init__(self, db: Session):
        self.db = db

    def create_organization(self, org_data: OrganizationCreate) -> OrganizationModel:
        """Create a new organization"""
        # Check if name already exists
        existing_org = self.db.query(OrganizationModel).filter(
            OrganizationModel.name == org_data.name
        ).first()
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization name already exists"
            )

        organization = OrganizationModel(
            name=org_data.name,
            description=org_data.description,
            contact_email=org_data.contact_email,
            contact_phone=org_data.contact_phone,
            address=org_data.address,
            website=org_data.website,
            is_active=org_data.is_active
        )

        self.db.add(organization)
        self.db.commit()
        self.db.refresh(organization)

        return organization

    def get_organization(self, org_id: UUID) -> OrganizationModel:
        """Get organization by ID"""
        organization = self.db.query(OrganizationModel).filter(
            OrganizationModel.id == org_id
        ).first()
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        return organization

    def get_organizations(self, skip: int = 0, limit: int = 100) -> List[OrganizationModel]:
        """Get all organizations with pagination"""
        if limit > 100:
            limit = 100  # Max limit
        return self.db.query(OrganizationModel).offset(skip).limit(limit).all()

    def update_organization(self, org_id: UUID, org_data: OrganizationUpdate) -> OrganizationModel:
        """Update organization"""
        organization = self.get_organization(org_id)

        # Check if name is being changed and if it's already taken
        if org_data.name and org_data.name != organization.name:
            existing_org = self.db.query(OrganizationModel).filter(
                OrganizationModel.name == org_data.name
            ).first()
            if existing_org and existing_org.id != org_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization name already exists"
                )

        # Update fields
        update_data = org_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(organization, field, value)

        organization.updated_at = func.now()

        self.db.commit()
        self.db.refresh(organization)

        return organization

    def delete_organization(self, org_id: UUID) -> dict:
        """Delete organization"""
        organization = self.get_organization(org_id)

        # Check if organization has users
        user_count = self.db.query(UserModel).filter(
            UserModel.organization_id == org_id
        ).count()

        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete organization with active users"
            )

        self.db.delete(organization)
        self.db.commit()

        return {"message": "Organization deleted successfully"}

    def get_organization_summary(self, org_id: UUID) -> OrganizationSummary:
        """Get organization summary with statistics"""
        organization = self.get_organization(org_id)

        # Count users in organization
        user_count = self.db.query(UserModel).filter(
            UserModel.organization_id == org_id
        ).count()

        # Count donations from organization users
        donation_count = self.db.query(DonationModel).filter(
            DonationModel.user_id.in_(
                self.db.query(UserModel.id).filter(UserModel.organization_id == org_id)
            )
        ).count()

        # Sum donation amounts
        total_amount = self.db.query(func.sum(DonationModel.amount_gtq)).filter(
            DonationModel.user_id.in_(
                self.db.query(UserModel.id).filter(UserModel.organization_id == org_id)
            ),
            DonationModel.status_id == 2  # Approved donations only
        ).scalar() or 0

        return OrganizationSummary(
            id=organization.id,
            name=organization.name,
            total_users=user_count,
            total_donations=donation_count,
            total_amount=float(total_amount)
        )

    def get_all_organization_summaries(self) -> List[OrganizationSummary]:
        """Get summaries for all organizations"""
        organizations = self.get_organizations()
        summaries = []

        for org in organizations:
            try:
                summary = self.get_organization_summary(org.id)
                summaries.append(summary)
            except Exception as e:
                # Log error but continue with other organizations
                print(f"Error getting summary for organization {org.id}: {e}")
                continue

        return summaries