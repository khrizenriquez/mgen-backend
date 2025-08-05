"""
SQLAlchemy models for database tables
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum

from app.infrastructure.database.database import Base
from app.domain.entities.donation import DonationStatus, DonationType


class DonationModel(Base):
    """
    SQLAlchemy model for donations table
    """
    __tablename__ = "donations"
    
    id = Column(Integer, primary_key=True, index=True)
    donor_name = Column(String(255), nullable=False)
    donor_email = Column(String(255), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    donation_type = Column(SQLEnum(DonationType), nullable=False)
    status = Column(SQLEnum(DonationStatus), nullable=False, default=DonationStatus.PENDING)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Donation(id={self.id}, amount={self.amount} {self.currency}, status={self.status})>"