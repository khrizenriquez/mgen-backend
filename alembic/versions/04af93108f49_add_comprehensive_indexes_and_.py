"""Add comprehensive indexes and constraints for performance and data integrity

Revision ID: 04af93108f49
Revises: 47c7306d848e
Create Date: 2025-09-02 01:15:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '04af93108f49'
down_revision = '47c7306d848e'
branch_labels = None
depends_on = None

# ---------- helpers ----------
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

def index_exists(name, schema=None):
    sql = sa.text("""
        SELECT 1
        FROM pg_indexes
        WHERE indexname = :n
          AND (:s IS NULL OR schemaname = :s)
        LIMIT 1
    """)
    return bool(_bind().execute(sql, {"n": name, "s": schema}).scalar())

def drop_constraint_if_exists(table, name, type_=None, schema=None):
    if constraint_exists(table, name, schema=schema):
        op.drop_constraint(name, table, type_=type_, schema=schema)

def create_unique_constraint_if_absent(table, name, columns, schema=None):
    # Postgres no tiene "ADD CONSTRAINT IF NOT EXISTS" => validamos por nombre
    if table_exists(table, schema=schema) and not constraint_exists(table, name, schema=schema):
        op.create_unique_constraint(name, table, columns, schema=schema)

def create_index_if_absent(name, table, columns, unique=False, schema=None):
    if table_exists(table, schema=schema) and not index_exists(name, schema=schema):
        op.create_index(name, table, columns, unique=unique, schema=schema)


def upgrade() -> None:
    # === DONATIONS: asegurar unicidad de correlation_id con operaciones seguras ===
    if table_exists('donations'):
        # Algunas ramas intentan quitar esta constraint; hazlo solo si existe
        drop_constraint_if_exists('donations', 'donations_correlation_id_key', type_='unique')

        # Si existe la columna correlation_id, vuelve a crear la unicidad si no está
        if column_exists('donations', 'correlation_id'):
            create_unique_constraint_if_absent('donations', 'donations_correlation_id_key', ['correlation_id'])

        # Índices adicionales seguros
        create_index_if_absent('ix_donations_created_at', 'donations', ['created_at'])
        create_index_if_absent('ix_donations_status_id', 'donations', ['status_id'])

    # === USERS: índices adicionales seguros ===
    if table_exists('users'):
        create_index_if_absent('ix_users_created_at', 'users', ['created_at'])

    # === PAYMENT_EVENTS: índices adicionales seguros ===
    if table_exists('payment_events'):
        create_index_if_absent('ix_payment_events_received_at', 'payment_events', ['received_at'])

    # === EMAIL_LOGS: índices adicionales seguros ===
    if table_exists('email_logs'):
        create_index_if_absent('ix_email_logs_created_at', 'email_logs', ['created_at'])


def downgrade() -> None:
    # Revertimos solo lo que esta revisión pudo haber creado
    if table_exists('email_logs') and index_exists('ix_email_logs_created_at'):
        op.drop_index('ix_email_logs_created_at', table_name='email_logs')

    if table_exists('payment_events') and index_exists('ix_payment_events_received_at'):
        op.drop_index('ix_payment_events_received_at', table_name='payment_events')

    if table_exists('users') and index_exists('ix_users_created_at'):
        op.drop_index('ix_users_created_at', table_name='users')

    if table_exists('donations'):
        if index_exists('ix_donations_status_id'):
            op.drop_index('ix_donations_status_id', table_name='donations')
        if index_exists('ix_donations_created_at'):
            op.drop_index('ix_donations_created_at', table_name='donations')
        # Quita la unique solo si fue creada por esta migración
        if constraint_exists('donations', 'donations_correlation_id_key'):
            op.drop_constraint('donations_correlation_id_key', 'donations', type_='unique')
