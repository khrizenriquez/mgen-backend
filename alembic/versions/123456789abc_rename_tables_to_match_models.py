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

    # Update foreign key references
    op.execute("ALTER TABLE app_user_role RENAME COLUMN user_id TO temp_user_id")
    op.execute("ALTER TABLE app_user_role RENAME COLUMN role_id TO temp_role_id")

    op.execute("ALTER TABLE app_user_role ADD COLUMN user_id UUID")
    op.execute("ALTER TABLE app_user_role ADD COLUMN role_id INTEGER")

    # Copy data with proper types
    op.execute("""
        UPDATE app_user_role
        SET user_id = temp_user_id::uuid,
            role_id = temp_role_id::integer
    """)

    # Drop old columns
    op.drop_column('app_user_role', 'temp_user_id')
    op.drop_column('app_user_role', 'temp_role_id')

    # Recreate constraints with new table names
    op.drop_constraint('user_roles_role_id_fkey', 'app_user_role', type_='foreignkey')
    op.create_foreign_key('fk_app_user_role_user_id', 'app_user_role', 'app_user', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_app_user_role_role_id', 'app_user_role', 'app_role', ['role_id'], ['id'], ondelete='CASCADE')

    # Update other foreign keys that reference the renamed tables
    op.drop_constraint('donor_contacts_user_id_fkey', 'donor_contacts', type_='foreignkey')
    op.create_foreign_key('fk_donor_contacts_user_id', 'donor_contacts', 'app_user', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Reverse the renames
    op.rename_table('app_user', 'users')
    op.rename_table('app_role', 'roles')
    op.rename_table('app_user_role', 'user_roles')

    # Update foreign key references back
    op.drop_constraint('fk_app_user_role_user_id', 'user_roles', type_='foreignkey')
    op.drop_constraint('fk_app_user_role_role_id', 'user_roles', type_='foreignkey')
    op.create_foreign_key('user_roles_role_id_fkey', 'user_roles', 'roles', ['role_id'], ['id'], ondelete='CASCADE')

    op.drop_constraint('fk_donor_contacts_user_id', 'donor_contacts', type_='foreignkey')
    op.create_foreign_key('donor_contacts_user_id_fkey', 'donor_contacts', 'users', ['user_id'], ['id'], ondelete='CASCADE')