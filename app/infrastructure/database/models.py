"""
SQLAlchemy models for database tables
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, UUID, ForeignKey, Boolean, JSON, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
import os

from app.infrastructure.database.database import Base

# Custom UUID type that uses String for SQLite (tests) and PostgreSQL UUID for production
class CustomUUID:
    def __new__(cls, as_uuid=True):
        # Use String for SQLite (tests), PostgreSQL UUID for production
        if os.getenv('TESTING') == 'true':
            return String
        else:
            return PostgreSQL_UUID(as_uuid=as_uuid)


class StatusCatalogModel(Base):
    """
    SQLAlchemy model for status_catalog table
    Manages all status definitions for the system
    """
    __tablename__ = "status_catalog"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(Text, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    donations = relationship("DonationModel", back_populates="status")
    payment_events = relationship("PaymentEventModel", back_populates="status")
    email_logs = relationship("EmailLogModel", back_populates="status")
    
    def __repr__(self):
        return f"<StatusCatalog(id={self.id}, code='{self.code}')>"


class OrganizationModel(Base):
    """
    SQLAlchemy model for organization table
    Manages organization information
    """
    __tablename__ = "organization"

    id = Column(CustomUUID(as_uuid=True), primary_key=True, index=True, server_default=func.gen_random_uuid())
    name = Column(Text, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    contact_email = Column(Text, nullable=True)
    contact_phone = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    website = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    users = relationship("UserModel", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"


class UserModel(Base):
    """
    SQLAlchemy model for users table
    Manages user authentication and identity
    """
    __tablename__ = "app_user"

    id = Column(CustomUUID(as_uuid=True), primary_key=True, index=True, server_default=func.gen_random_uuid())
    email = Column(Text, nullable=False, unique=True, index=True)
    password_hash = Column(Text, nullable=False)
    email_verified = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    phone = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    preferences = Column(JSON, nullable=True, default=dict)  # User preferences as JSON
    organization_id = Column(CustomUUID(as_uuid=True), ForeignKey('organization.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    donations = relationship("DonationModel", back_populates="user")
    user_roles = relationship("UserRoleModel", back_populates="user", cascade="all, delete-orphan")
    donor_contact = relationship("DonorContactModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    organization = relationship("OrganizationModel", back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class RoleModel(Base):
    """
    SQLAlchemy model for roles table
    Manages user roles and permissions
    """
    __tablename__ = "app_role"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    user_roles = relationship("UserRoleModel", back_populates="role", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"


class UserRoleModel(Base):
    """
    SQLAlchemy model for user_roles table
    Junction table for many-to-many user-role relationship
    """
    __tablename__ = "app_user_role"
    
    user_id = Column(CustomUUID(as_uuid=True), ForeignKey('app_user.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    role_id = Column(Integer, ForeignKey('app_role.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    user = relationship("UserModel", back_populates="user_roles")
    role = relationship("RoleModel", back_populates="user_roles")
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class DonationModel(Base):
    """
    SQLAlchemy model for donations table
    Matches the real database schema from schema.sql
    """
    __tablename__ = "donation"
    
    id = Column(CustomUUID(as_uuid=True), primary_key=True, index=True, server_default=func.gen_random_uuid())
    amount_gtq = Column(Numeric(12, 2), nullable=False, index=True)
    status_id = Column(Integer, ForeignKey('status_catalog.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    donor_email = Column(Text, nullable=False, index=True)
    donor_name = Column(Text, nullable=True)
    donor_nit = Column(Text, nullable=True)
    user_id = Column(CustomUUID(as_uuid=True), ForeignKey('app_user.id'), nullable=True)
    payu_order_id = Column(Text, nullable=True)
    reference_code = Column(Text, nullable=False, unique=True, index=True)
    correlation_id = Column(Text, nullable=False, unique=True, index=True)
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('amount_gtq > 0', name='check_amount_positive'),
        # Email validation constraint - simplified for cross-database compatibility
        CheckConstraint("donor_email LIKE '%@%'", name='check_valid_email_basic'),
    )
    
    # Relationships
    status = relationship("StatusCatalogModel", back_populates="donations")
    user = relationship("UserModel", back_populates="donations")
    payment_events = relationship("PaymentEventModel", back_populates="donation", cascade="all, delete-orphan")
    email_logs = relationship("EmailLogModel", back_populates="donation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Donation(id={self.id}, amount_gtq={self.amount_gtq}, status_id={self.status_id})>"


class PaymentEventModel(Base):
    """
    SQLAlchemy model for payment_events table
    Manages payment webhook and reconciliation events
    """
    __tablename__ = "payment_event"
    
    id = Column(CustomUUID(as_uuid=True), primary_key=True, index=True, server_default=func.gen_random_uuid())
    donation_id = Column(CustomUUID(as_uuid=True), ForeignKey('donation.id', ondelete='RESTRICT'), nullable=False, index=True)
    event_id = Column(Text, nullable=False, unique=True, index=True)
    source = Column(Text, nullable=False, index=True)  # 'webhook' or 'recon'
    status_id = Column(Integer, ForeignKey('status_catalog.id'), nullable=False, index=True)
    payload_raw = Column(JSON, nullable=False, default={})
    signature_ok = Column(Boolean, nullable=False, default=False, index=True)
    received_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("source IN ('webhook', 'recon')", name='check_valid_source'),
        # Simplified time constraint for cross-database compatibility
        CheckConstraint('received_at IS NOT NULL', name='check_received_at_not_null'),
    )
    
    # Relationships
    donation = relationship("DonationModel", back_populates="payment_events")
    status = relationship("StatusCatalogModel", back_populates="payment_events")
    
    def __repr__(self):
        return f"<PaymentEvent(id={self.id}, event_id='{self.event_id}', source='{self.source}')>"


class EmailLogModel(Base):
    """
    SQLAlchemy model for email_logs table
    Manages email sending and delivery tracking
    """
    __tablename__ = "email_log"
    
    id = Column(CustomUUID(as_uuid=True), primary_key=True, index=True, server_default=func.gen_random_uuid())
    donation_id = Column(CustomUUID(as_uuid=True), ForeignKey('donation.id', ondelete='RESTRICT'), nullable=False, index=True)
    to_email = Column(Text, nullable=False, index=True)
    type = Column(Text, nullable=False, index=True)  # 'receipt' or 'resend'
    status_id = Column(Integer, ForeignKey('status_catalog.id'), nullable=False, index=True)
    provider_msg_id = Column(Text, unique=True, nullable=True, index=True)
    attempt = Column(Integer, nullable=False, default=0, index=True)
    last_error = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    provider_event_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("type IN ('receipt', 'resend')", name='check_valid_email_type'),
        CheckConstraint('attempt >= 0', name='check_attempt_non_negative'),
        # Email validation constraint - simplified for cross-database compatibility
        CheckConstraint("to_email LIKE '%@%'", name='check_valid_email_format_basic'),
    )
    
    # Relationships
    donation = relationship("DonationModel", back_populates="email_logs")
    status = relationship("StatusCatalogModel", back_populates="email_logs")
    
    def __repr__(self):
        return f"<EmailLog(id={self.id}, type='{self.type}', to_email='{self.to_email}')>"


class DonorContactModel(Base):
    """
    SQLAlchemy model for donor_contacts table
    Manages additional donor contact information
    """
    __tablename__ = "donor_contact"
    
    user_id = Column(CustomUUID(as_uuid=True), ForeignKey('app_user.id', ondelete='CASCADE'), primary_key=True)
    phone_number = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    contact_preference = Column(Text, nullable=True, index=True)  # 'email', 'phone', 'mail'
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    user = relationship("UserModel", back_populates="donor_contact")
    
    def __repr__(self):
        return f"<DonorContact(user_id={self.user_id}, preference='{self.contact_preference}')>"


class SimpleUserModel(Base):
    """
    Simple User model for CRUD POC
    """
    __tablename__ = "simple_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SimpleUser(id={self.id}, email='{self.email}', name='{self.first_name} {self.last_name}')>"