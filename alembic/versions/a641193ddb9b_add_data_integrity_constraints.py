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

# ---------- helpers (compatibles con Py 3.8) ----------
def _bind():
    return op.get_bind()

def table_exists(table_name, schema=None):
    insp = sa.inspect(_bind())
    return insp.has_table(table_name, schema=schema)

def column_exists(table, column, schema=None):
    sql = sa.text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = :t
          AND column_name = :c
          AND (:s IS NULL OR table_schema = :s)
        LIMIT 1
    """)
    return bool(_bind().execute(sql, {"t": table, "c": column, "s": schema}).scalar())

def constraint_exists(table, name, schema=None):
    sql = sa.text("""
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_name = :t
          AND constraint_name = :n
          AND (:s IS NULL OR table_schema = :s)
        LIMIT 1
    """)
    return bool(_bind().execute(sql, {"t": table, "n": name, "s": schema}).scalar())


def upgrade() -> None:
    # ----- donations: amount_gtq > 0 -----
    if table_exists('donations') and column_exists('donations', 'amount_gtq'):
        if not constraint_exists('donations', 'chk_donations_amount_positive'):
            op.execute("""
                ALTER TABLE donations
                ADD CONSTRAINT chk_donations_amount_positive
                CHECK (amount_gtq > 0)
            """)

    # ----- donations: email format -----
    if table_exists('donations') and column_exists('donations', 'donor_email'):
        if not constraint_exists('donations', 'chk_donations_email_format'):
            op.execute("""
                ALTER TABLE donations
                ADD CONSTRAINT chk_donations_email_format
                CHECK (donor_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')
            """)

    # ----- donations: reference_code format -----
    if table_exists('donations') and column_exists('donations', 'reference_code'):
        if not constraint_exists('donations', 'chk_donations_reference_code_format'):
            op.execute("""
                ALTER TABLE donations
                ADD CONSTRAINT chk_donations_reference_code_format
                CHECK (reference_code ~ '^[A-Za-z0-9_-]+$' AND length(reference_code) >= 3)
            """)

    # ----- payment_events: source IN ('webhook','recon') -----
    if table_exists('payment_events') and column_exists('payment_events', 'source'):
        if not constraint_exists('payment_events', 'chk_payment_events_source_valid'):
            op.execute("""
                ALTER TABLE payment_events
                ADD CONSTRAINT chk_payment_events_source_valid
                CHECK (source IN ('webhook', 'recon'))
            """)

    # ----- email_logs: type IN ('receipt','resend') -----
    if table_exists('email_logs') and column_exists('email_logs', 'type'):
        if not constraint_exists('email_logs', 'chk_email_logs_type_valid'):
            op.execute("""
                ALTER TABLE email_logs
                ADD CONSTRAINT chk_email_logs_type_valid
                CHECK (type IN ('receipt', 'resend'))
            """)

    # ----- email_logs: attempt >= 0 -----
    if table_exists('email_logs') and column_exists('email_logs', 'attempt'):
        if not constraint_exists('email_logs', 'chk_email_logs_attempt_positive'):
            op.execute("""
                ALTER TABLE email_logs
                ADD CONSTRAINT chk_email_logs_attempt_positive
                CHECK (attempt >= 0)
            """)


def downgrade() -> None:
    # Quitar sólo si existen
    if table_exists('email_logs') and constraint_exists('email_logs', 'chk_email_logs_attempt_positive'):
        op.execute("ALTER TABLE email_logs DROP CONSTRAINT chk_email_logs_attempt_positive")
    if table_exists('email_logs') and constraint_exists('email_logs', 'chk_email_logs_type_valid'):
        op.execute("ALTER TABLE email_logs DROP CONSTRAINT chk_email_logs_type_valid")
    if table_exists('payment_events') and constraint_exists('payment_events', 'chk_payment_events_source_valid'):
        op.execute("ALTER TABLE payment_events DROP CONSTRAINT chk_payment_events_source_valid")
    if table_exists('donations') and constraint_exists('donations', 'chk_donations_reference_code_format'):
        op.execute("ALTER TABLE donations DROP CONSTRAINT chk_donations_reference_code_format")
    if table_exists('donations') and constraint_exists('donations', 'chk_donations_email_format'):
        op.execute("ALTER TABLE donations DROP CONSTRAINT chk_donations_email_format")
    if table_exists('donations') and constraint_exists('donations', 'chk_donations_amount_positive'):
        op.execute("ALTER TABLE donations DROP CONSTRAINT chk_donations_amount_positive")
