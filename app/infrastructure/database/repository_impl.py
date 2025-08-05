"""
SQLAlchemy implementation of donation repository
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domain.entities.donation import Donation, DonationStatus, DonationType
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
            donor_name=model.donor_name,
            donor_email=model.donor_email,
            amount=model.amount,
            currency=model.currency,
            donation_type=model.donation_type,
            status=model.status,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at
        )
    
    def _entity_to_model(self, donation: Donation) -> DonationModel:
        """Convert domain entity to SQLAlchemy model"""
        return DonationModel(
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
            completed_at=donation.completed_at
        )
    
    async def create(self, donation: Donation) -> Donation:
        """Create a new donation"""
        model = self._entity_to_model(donation)
        model.id = None  # Let database generate ID
        
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        return self._model_to_entity(model)
    
    async def get_by_id(self, donation_id: int) -> Optional[Donation]:
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
        donation_type: Optional[DonationType] = None
    ) -> List[Donation]:
        """Get all donations with optional filtering"""
        query = self.db.query(DonationModel)
        
        if status:
            query = query.filter(DonationModel.status == status)
        
        if donation_type:
            query = query.filter(DonationModel.donation_type == donation_type)
        
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
        model.donor_name = donation.donor_name
        model.donor_email = donation.donor_email
        model.amount = donation.amount
        model.currency = donation.currency
        model.donation_type = donation.donation_type
        model.status = donation.status
        model.description = donation.description
        model.updated_at = donation.updated_at
        model.completed_at = donation.completed_at
        
        self.db.commit()
        self.db.refresh(model)
        
        return self._model_to_entity(model)
    
    async def delete(self, donation_id: int) -> bool:
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
            func.coalesce(func.sum(DonationModel.amount), 0)
        ).filter(DonationModel.status == status).scalar()
        
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
            DonationModel.status == status
        ).count()