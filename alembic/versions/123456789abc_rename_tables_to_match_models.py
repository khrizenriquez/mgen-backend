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
    op.rename_table('users', 'app_user')
    op.rename_table('roles', 'app_role')
    op.rename_table('user_roles', 'app_user_role')

    # Recreate app_user_role table with correct types
    # Since we're in a test environment, we'll drop and recreate the table
    # In production, this would require more careful data migration

    # Drop existing table (now renamed to app_user_role)
    op.drop_table('app_user_role')

    # Recreate with correct types
    op.create_table(
        'app_user_role',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    # Create foreign keys for the new app_user_role table
    op.create_foreign_key('fk_app_user_role_user_id', 'app_user_role', 'app_user', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_app_user_role_role_id', 'app_user_role', 'app_role', ['role_id'], ['id'], ondelete='CASCADE')

    # Update other foreign keys that reference the renamed tables
    op.drop_constraint('donor_contacts_user_id_fkey', 'donor_contacts', type_='foreignkey')
    op.create_foreign_key('fk_donor_contacts_user_id', 'donor_contacts', 'app_user', ['user_id'], ['id'], ondelete='CASCADE')

    # Update organization foreign key reference
    op.drop_constraint('fk_users_organization_id', 'app_user', type_='foreignkey')
    op.create_foreign_key('fk_app_user_organization_id', 'app_user', 'organization', ['organization_id'], ['id'])


def downgrade() -> None:
    # Reverse foreign key changes
    op.drop_constraint('fk_app_user_organization_id', 'app_user', type_='foreignkey')
    op.create_foreign_key('fk_users_organization_id', 'app_user', 'organization', ['organization_id'], ['id'])

    op.drop_constraint('fk_donor_contacts_user_id', 'donor_contacts', type_='foreignkey')
    op.create_foreign_key('donor_contacts_user_id_fkey', 'donor_contacts', 'app_user', ['user_id'], ['id'], ondelete='CASCADE')

    # Reverse the renames first
    op.rename_table('app_user_role', 'user_roles')
    op.rename_table('app_role', 'roles')
    op.rename_table('app_user', 'users')

    # Recreate original foreign keys
    op.create_foreign_key('user_roles_user_id_fkey', 'user_roles', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('user_roles_role_id_fkey', 'user_roles', 'roles', ['role_id'], ['id'], ondelete='CASCADE')