"""
SQLAlchemy models for database tables
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, UUID, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from datetime import datetime
from enum import Enum

from app.infrastructure.database.database import Base


class DonationModel(Base):
    """
    SQLAlchemy model for donations table
    Matches the real database schema from schema.sql
    """
    __tablename__ = "donations"
    
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, index=True, server_default=func.gen_random_uuid())
    amount_gtq = Column(Numeric(12, 2), nullable=False)
    status_id = Column(Integer, ForeignKey('status_catalog.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    donor_email = Column(Text, nullable=False)
    donor_name = Column(Text, nullable=True)
    donor_nit = Column(Text, nullable=True)
    user_id = Column(PostgreSQL_UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    payu_order_id = Column(Text, nullable=True)
    reference_code = Column(Text, nullable=False, unique=True)
    correlation_id = Column(Text, nullable=False, unique=True)
    
    def __repr__(self):
        return f"<Donation(id={self.id}, amount_gtq={self.amount_gtq}, status_id={self.status_id})>"