"""Initial migration - create all tables

Revision ID: 4a9d440c02ab
Revises:
Create Date: 2025-09-02 01:02:39.063456
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4a9d440c02ab'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------- TABLES ----------
    op.create_table(
        'status_catalog',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('email', sa.String(320), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'roles',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'donations',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('status_id', sa.Integer, sa.ForeignKey('status_catalog.id', ondelete='SET NULL'), nullable=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'donor_contacts',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('contact_preference', sa.String(50), nullable=True),  # email / phone / none ...
        sa.Column('value', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role_id', sa.Integer, sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'email_logs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('donation_id', sa.Integer, sa.ForeignKey('donations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status_id', sa.Integer, sa.ForeignKey('status_catalog.id', ondelete='SET NULL'), nullable=True),
        sa.Column('type', sa.String(50), nullable=True),  # e.g. receipt, reminder
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'payment_events',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('donation_id', sa.Integer, sa.ForeignKey('donations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_id', sa.String(255), nullable=False),
        sa.Column('source', sa.String(50), nullable=True),  # stripe, paypal, etc.
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('payload_raw', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )

    # ---------- INDEXES & CONSTRAINTS ----------
    # status_catalog
    op.create_index(op.f('ix_status_catalog_id'), 'status_catalog', ['id'], unique=False)
    op.create_index(op.f('ix_status_catalog_code'), 'status_catalog', ['code'], unique=True)

    # users
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # roles
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)

    # donations
    op.create_index(op.f('ix_donations_id'), 'donations', ['id'], unique=False)
    # (histórico referenciado)
    op.create_index('idx_donations_statusid_created_at', 'donations', ['status_id', 'created_at'], unique=False)

    # donor_contacts
    op.create_index(op.f('ix_donor_contacts_contact_preference'), 'donor_contacts', ['contact_preference'], unique=False)

    # email_logs
    op.create_index(op.f('ix_email_logs_id'), 'email_logs', ['id'], unique=False)
    op.create_index(op.f('ix_email_logs_type'), 'email_logs', ['type'], unique=False)
    # (histórico referenciado)
    op.create_index('idx_email_logs_donation_id_statusid', 'email_logs', ['donation_id', 'status_id'], unique=False)

    # payment_events
    op.create_index(op.f('ix_payment_events_id'), 'payment_events', ['id'], unique=False)
    op.create_index(op.f('ix_payment_events_source'), 'payment_events', ['source'], unique=False)
    op.create_index(op.f('ix_payment_events_event_id'), 'payment_events', ['event_id'], unique=True)


def downgrade() -> None:
    # Drop indexes before tables (reverse order where helpful)
    op.drop_index(op.f('ix_payment_events_event_id'), table_name='payment_events')
    op.drop_index(op.f('ix_payment_events_source'), table_name='payment_events')
    op.drop_index(op.f('ix_payment_events_id'), table_name='payment_events')

    op.drop_index(op.f('ix_email_logs_type'), table_name='email_logs')
    op.drop_index(op.f('ix_email_logs_id'), table_name='email_logs')
    op.drop_index('idx_email_logs_donation_id_statusid', table_name='email_logs')

    op.drop_index(op.f('ix_donor_contacts_contact_preference'), table_name='donor_contacts')

    op.drop_index('idx_donations_statusid_created_at', table_name='donations')
    op.drop_index(op.f('ix_donations_id'), table_name='donations')

    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_index(op.f('ix_roles_id'), table_name='roles')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')

    op.drop_index(op.f('ix_status_catalog_code'), table_name='status_catalog')
    op.drop_index(op.f('ix_status_catalog_id'), table_name='status_catalog')

    # Drop tables (FK dependents first)
    op.drop_table('payment_events')
    op.drop_table('email_logs')
    op.drop_table('user_roles')
    op.drop_table('donor_contacts')
    op.drop_table('donations')
    op.drop_table('roles')
    op.drop_table('users')
    op.drop_table('status_catalog')
