"""add_user_profile_fields

Revision ID: b722440e5ca8
Revises: 123456789abc
Create Date: 2025-10-18 03:51:26.619603

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b722440e5ca8'
down_revision = '123456789abc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add profile fields to app_user table
    op.add_column('app_user', sa.Column('first_name', sa.Text(), nullable=True))
    op.add_column('app_user', sa.Column('last_name', sa.Text(), nullable=True))
    op.add_column('app_user', sa.Column('phone', sa.Text(), nullable=True))
    op.add_column('app_user', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('app_user', sa.Column('preferences', sa.JSON(), nullable=True, default=dict))


def downgrade() -> None:
    # Remove profile fields from app_user table
    op.drop_column('app_user', 'preferences')
    op.drop_column('app_user', 'address')
    op.drop_column('app_user', 'phone')
    op.drop_column('app_user', 'last_name')
    op.drop_column('app_user', 'first_name')