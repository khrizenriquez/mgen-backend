"""Rename tables to match model definitions

Revision ID: rename_tables
Revises: 0f4dd98d57c0
Create Date: 2025-10-04 01:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '123456789abc'
down_revision = '0f4dd98d57c0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename tables to match model definitions
    op.rename_table('users', 'app_user_old')
    op.rename_table('roles', 'app_role')
    op.rename_table('user_roles', 'app_user_role_old')

    # Drop foreign key constraints that reference the old tables BEFORE dropping them
    # This prevents "DependentObjectsStillExist" errors
    op.drop_constraint('donor_contacts_user_id_fkey', 'donor_contacts', type_='foreignkey')
    op.drop_constraint('user_roles_user_id_fkey', 'app_user_role_old', type_='foreignkey')
    op.drop_constraint('user_roles_role_id_fkey', 'app_user_role_old', type_='foreignkey')
    
    # Drop organization foreign key if it exists
    try:
        op.drop_constraint('fk_users_organization_id', 'app_user_old', type_='foreignkey')
    except Exception:
        # Constraint might not exist in all environments
        pass

    # Recreate tables with correct types (since this is for testing, we can drop and recreate)
    # In production, this would require proper data migration

    # Recreate app_user with correct UUID type
    op.create_table(
        'app_user',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Recreate app_user_role with correct types
    op.create_table(
        'app_user_role',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Now we can safely drop old tables since foreign keys are removed
    op.drop_table('app_user_old')
    op.drop_table('app_user_role_old')

    # Create foreign keys for the new tables
    op.create_foreign_key('fk_app_user_role_user_id', 'app_user_role', 'app_user', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_app_user_role_role_id', 'app_user_role', 'app_role', ['role_id'], ['id'], ondelete='CASCADE')

    # Update other foreign keys that reference the new tables
    op.create_foreign_key('fk_donor_contacts_user_id', 'donor_contacts', 'app_user', ['user_id'], ['id'], ondelete='CASCADE')

    # Create organization foreign key reference for new app_user table
    op.create_foreign_key('fk_app_user_organization_id', 'app_user', 'organization', ['organization_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key constraints BEFORE dropping tables
    op.drop_constraint('fk_app_user_organization_id', 'app_user', type_='foreignkey')
    op.drop_constraint('fk_donor_contacts_user_id', 'donor_contacts', type_='foreignkey')
    op.drop_constraint('fk_app_user_role_user_id', 'app_user_role', type_='foreignkey')
    op.drop_constraint('fk_app_user_role_role_id', 'app_user_role', type_='foreignkey')

    # Now we can safely drop current tables
    op.drop_table('app_user_role')
    op.drop_table('app_user')

    # Recreate original tables with INTEGER IDs
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Reverse role table rename
    op.rename_table('app_role', 'roles')

    # Recreate original foreign keys
    op.create_foreign_key('user_roles_user_id_fkey', 'user_roles', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('user_roles_role_id_fkey', 'user_roles', 'roles', ['role_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('donor_contacts_user_id_fkey', 'donor_contacts', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    
    # Recreate organization foreign key if needed
    try:
        op.create_foreign_key('fk_users_organization_id', 'users', 'organization', ['organization_id'], ['id'])
    except Exception:
        # Constraint might not be needed in all environments
        pass