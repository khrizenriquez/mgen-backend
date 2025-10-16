"""
SQLAlchemy implementation of donation repository
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domain.entities.donation import Donation, DonationStatus
from app.domain.repositories.donation_repository import DonationRepository
from app.infrastructure.database.models import DonationModel


class SQLAlchemyDonationRepository(DonationRepository):
    """
    Concrete implementation of DonationRepository using SQLAlchemy
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def _model_to_entity(self, model: DonationModel) -> Donation:
        """Convert SQLAlchemy model to domain entity"""
        return Donation(
            id=model.id,
            amount_gtq=model.amount_gtq,
            status_id=model.status_id,
            donor_email=model.donor_email,
            donor_name=model.donor_name,
            donor_nit=model.donor_nit,
            user_id=model.user_id,
            payu_order_id=model.payu_order_id,
            reference_code=model.reference_code,
            correlation_id=model.correlation_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            paid_at=model.paid_at
        )
    
    def _entity_to_model(self, donation: Donation) -> DonationModel:
        """Convert domain entity to SQLAlchemy model"""
        return DonationModel(
            id=donation.id,
            amount_gtq=donation.amount_gtq,
            status_id=donation.status_id,
            donor_email=donation.donor_email,
            donor_name=donation.donor_name,
            donor_nit=donation.donor_nit,
            user_id=donation.user_id,
            payu_order_id=donation.payu_order_id,
            reference_code=donation.reference_code,
            correlation_id=donation.correlation_id,
            created_at=donation.created_at,
            updated_at=donation.updated_at,
            paid_at=donation.paid_at
        )
    
    async def create(self, donation: Donation) -> Donation:
        """Create a new donation"""
        model = self._entity_to_model(donation)
        model.id = None  # Let database generate ID
        
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        return self._model_to_entity(model)
    
    async def get_by_id(self, donation_id: UUID) -> Optional[Donation]:
        """Get donation by ID"""
        model = self.db.query(DonationModel).filter(
            DonationModel.id == donation_id
        ).first()
        
        if model:
            return self._model_to_entity(model)
        return None
    
    async def get_by_email(self, email: str) -> List[Donation]:
        """Get all donations by donor email"""
        models = self.db.query(DonationModel).filter(
            DonationModel.donor_email == email
        ).order_by(DonationModel.created_at.desc()).all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[DonationStatus] = None,
        organization_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> List[Donation]:
        """Get all donations with optional filtering"""
        from app.infrastructure.database.models import UserModel

        query = self.db.query(DonationModel)

        if status:
            query = query.filter(DonationModel.status_id == status.value)

        if organization_id:
            # Join with UserModel to filter by organization
            query = query.join(UserModel, DonationModel.user_id == UserModel.id).filter(
                UserModel.organization_id == organization_id
            )

        if user_id:
            query = query.filter(DonationModel.user_id == user_id)

        models = query.order_by(
            DonationModel.created_at.desc()
        ).offset(offset).limit(limit).all()

        return [self._model_to_entity(model) for model in models]
    
    async def update(self, donation: Donation) -> Donation:
        """Update an existing donation"""
        model = self.db.query(DonationModel).filter(
            DonationModel.id == donation.id
        ).first()
        
        if not model:
            raise ValueError(f"Donation with ID {donation.id} not found")
        
        # Update fields
        model.amount_gtq = donation.amount_gtq
        model.status_id = donation.status_id
        model.donor_email = donation.donor_email
        model.donor_name = donation.donor_name
        model.donor_nit = donation.donor_nit
        model.user_id = donation.user_id
        model.payu_order_id = donation.payu_order_id
        model.reference_code = donation.reference_code
        model.correlation_id = donation.correlation_id
        model.updated_at = donation.updated_at
        model.paid_at = donation.paid_at
        
        self.db.commit()
        self.db.refresh(model)
        
        return self._model_to_entity(model)
    
    async def delete(self, donation_id: UUID) -> bool:
        """Delete a donation"""
        model = self.db.query(DonationModel).filter(
            DonationModel.id == donation_id
        ).first()
        
        if model:
            self.db.delete(model)
            self.db.commit()
            return True
        
        return False
    
    async def get_total_amount_by_status(self, status: DonationStatus) -> Decimal:
        """Get total amount for donations with specific status"""
        result = self.db.query(
            func.coalesce(func.sum(DonationModel.amount_gtq), 0)
        ).filter(DonationModel.status_id == status.value).scalar()
        
        return Decimal(str(result or 0))
    
    async def get_donations_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Donation]:
        """Get donations within date range"""
        models = self.db.query(DonationModel).filter(
            DonationModel.created_at >= start_date,
            DonationModel.created_at <= end_date
        ).order_by(DonationModel.created_at.desc()).all()
        
        return [self._model_to_entity(model) for model in models]
    
    async def count_by_status(self, status: DonationStatus) -> int:
        """Count donations by status"""
        return self.db.query(DonationModel).filter(
            DonationModel.status_id == status.value
        ).count()