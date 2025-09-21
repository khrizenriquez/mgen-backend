"""Add data integrity constraints

Revision ID: a641193ddb9b
Revises: 04af93108f49
Create Date: 2025-09-02 01:26:37.479659

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a641193ddb9b'
down_revision = '04af93108f49'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add constraints for donations table
    op.execute("""
        ALTER TABLE donations 
        ADD CONSTRAINT chk_donations_amount_positive 
        CHECK (amount_gtq > 0);
    """)
    
    op.execute("""
        ALTER TABLE donations 
        ADD CONSTRAINT chk_donations_email_format 
        CHECK (donor_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$');
    """)
    
    op.execute("""
        ALTER TABLE donations 
        ADD CONSTRAINT chk_donations_reference_code_format 
        CHECK (reference_code ~ '^[A-Za-z0-9_-]+$' AND length(reference_code) >= 3);
    """)
    
    # Add constraints for payment_events table
    op.execute("""
        ALTER TABLE payment_events 
        ADD CONSTRAINT chk_payment_events_source_valid 
        CHECK (source IN ('webhook', 'recon'));
    """)
    
    # Add constraints for email_logs table  
    op.execute("""
        ALTER TABLE email_logs 
        ADD CONSTRAINT chk_email_logs_type_valid 
        CHECK (type IN ('receipt', 'resend'));
    """)
    
    op.execute("""
        ALTER TABLE email_logs 
        ADD CONSTRAINT chk_email_logs_attempt_positive 
        CHECK (attempt >= 0);
    """)


def downgrade() -> None:
    # Remove constraints in reverse order
    op.execute("ALTER TABLE email_logs DROP CONSTRAINT IF EXISTS chk_email_logs_attempt_positive;")
    op.execute("ALTER TABLE email_logs DROP CONSTRAINT IF EXISTS chk_email_logs_type_valid;")
    op.execute("ALTER TABLE payment_events DROP CONSTRAINT IF EXISTS chk_payment_events_source_valid;")
    op.execute("ALTER TABLE donations DROP CONSTRAINT IF EXISTS chk_donations_reference_code_format;")
    op.execute("ALTER TABLE donations DROP CONSTRAINT IF EXISTS chk_donations_email_format;")
    op.execute("ALTER TABLE donations DROP CONSTRAINT IF EXISTS chk_donations_amount_positive;")