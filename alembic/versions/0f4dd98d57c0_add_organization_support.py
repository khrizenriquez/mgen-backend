"""add_organization_support

Revision ID: 0f4dd98d57c0
Revises: 3acc0fa3037e
Create Date: 2025-10-02 02:56:12.401651

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0f4dd98d57c0'
down_revision = '3acc0fa3037e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organization table
    op.create_table(
        'organization',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.Text(), nullable=True),
        sa.Column('contact_phone', sa.Text(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('website', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Add organization_id column to users (will be renamed to app_user later)
    op.add_column('users', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_users_organization_id',
        'users', 'organization',
        ['organization_id'], ['id']
    )

    # Insert default organization
    op.execute("""
        INSERT INTO organization (id, name, description, contact_email, is_active)
        VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Fundación Donaciones Guatemala',
                'Organización principal de donaciones en Guatemala', 'contacto@donacionesgt.org', TRUE)
        ON CONFLICT (id) DO NOTHING
    """)

    # Insert roles if they don't exist
    op.execute("""
        INSERT INTO roles (name)
        VALUES
            ('ADMIN'),
            ('ORGANIZATION'),
            ('AUDITOR'),
            ('DONOR'),
            ('USER')
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    # Remove organization_id foreign key and column
    op.drop_constraint('fk_users_organization_id', 'users', type_='foreignkey')
    op.drop_column('users', 'organization_id')

    # Drop organization table
    op.drop_table('organization')