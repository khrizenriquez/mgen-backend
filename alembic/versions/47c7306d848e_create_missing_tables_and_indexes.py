"""Create missing tables and indexes

Revision ID: 47c7306d848e
Revises: 4a9d440c02ab
Create Date: 2025-09-02 01:03:10.210841
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '47c7306d848e'
down_revision = '4a9d440c02ab'
branch_labels = None
depends_on = None


# ---------- helpers ----------
def _bind():
    return op.get_bind()

def table_exists(table_name: str, schema: str = None) -> bool:
    insp = sa.inspect(_bind())
    return insp.has_table(table_name, schema=schema)

def index_exists(index_name: str, schema: str = None) -> bool:
    sql = sa.text("""
        SELECT 1
        FROM pg_indexes
        WHERE indexname = :name
          AND (:schema IS NULL OR schemaname = :schema)
        LIMIT 1
    """)
    return bool(_bind().execute(sql, {"name": index_name, "schema": schema}).scalar())

def fk_exists(constraint_name: str, table: str, schema: str = None) -> bool:
    sql = sa.text("""
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
          AND table_name = :table
          AND constraint_name = :name
          AND (:schema IS NULL OR table_schema = :schema)
        LIMIT 1
    """)
    return bool(_bind().execute(sql, {"table": table, "name": constraint_name, "schema": schema}).scalar())

def drop_index_if_exists(index_name: str, schema: str = None):
    if index_exists(index_name, schema=schema):
        op.drop_index(index_name, schema=schema)

def drop_constraint_if_exists(table: str, constraint_name: str, type_: str = 'foreignkey', schema: str = None):
    sql = sa.text("""
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_name = :table
          AND constraint_name = :name
          AND (:schema IS NULL OR table_schema = :schema)
        LIMIT 1
    """)
    if _bind().execute(sql, {"table": table, "name": constraint_name, "schema": schema}).scalar():
        op.drop_constraint(constraint_name, table, type_=type_, schema=schema)

def create_index_if_absent(index_name: str, table: str, columns, unique: bool = False, schema: str = None):
    if table_exists(table, schema=schema) and not index_exists(index_name, schema=schema):
        op.create_index(index_name, table, columns, unique=unique, schema=schema)

def create_fk_if_absent(constraint_name: str, source_table: str, referent_table: str,
                        local_cols, remote_cols, ondelete: str = None,
                        source_schema: str = None, referent_schema: str = None):
    if table_exists(source_table, schema=source_schema) and table_exists(referent_table, schema=referent_schema):
        if not fk_exists(constraint_name, source_table, schema=source_schema):
            op.create_foreign_key(constraint_name, source_table, referent_table,
                                  local_cols, remote_cols,
                                  source_schema=source_schema, referent_schema=referent_schema,
                                  ondelete=ondelete)


def upgrade() -> None:
    # -------- DROPS condicionales --------
    drop_index_if_exists('idx_donations_statusid_created_at')
    drop_index_if_exists('idx_email_logs_donation_id_statusid')
    drop_index_if_exists('idx_payment_events_donation_id_received_at')

    drop_constraint_if_exists('payment_events', 'payment_events_event_id_key', type_='unique')
    drop_constraint_if_exists('roles', 'roles_name_key', type_='unique')
    drop_constraint_if_exists('status_catalog', 'status_catalog_code_key', type_='unique')
    drop_constraint_if_exists('user_roles', 'user_roles_role_id_fkey', type_='foreignkey')
    drop_constraint_if_exists('users', 'users_email_key', type_='unique')
    drop_index_if_exists('users_email_lower_uidx')

    # Skips de alter si quieres mantener limpio
    # if table_exists('payment_events'):
    #     pass
    # if table_exists('roles'):
    #     pass

    # -------- CREATES solo si NO existen --------
    create_index_if_absent(op.f('ix_donations_id'), 'donations', ['id'])
    create_index_if_absent(op.f('ix_donor_contacts_contact_preference'), 'donor_contacts', ['contact_preference'])

    create_index_if_absent(op.f('ix_email_logs_id'), 'email_logs', ['id'])
    create_index_if_absent(op.f('ix_email_logs_type'), 'email_logs', ['type'])

    create_index_if_absent(op.f('ix_payment_events_event_id'), 'payment_events', ['event_id'], unique=True)
    create_index_if_absent(op.f('ix_payment_events_id'), 'payment_events', ['id'])
    create_index_if_absent(op.f('ix_payment_events_source'), 'payment_events', ['source'])

    create_index_if_absent(op.f('ix_roles_id'), 'roles', ['id'])
    create_index_if_absent(op.f('ix_roles_name'), 'roles', ['name'], unique=True)

    create_index_if_absent(op.f('ix_status_catalog_code'), 'status_catalog', ['code'], unique=True)
    create_index_if_absent(op.f('ix_status_catalog_id'), 'status_catalog', ['id'])

    # Usa un nombre explícito para la FK y evita duplicarla
    create_fk_if_absent('user_roles_role_id_fkey', 'user_roles', 'roles', ['role_id'], ['id'], ondelete='CASCADE')

    create_index_if_absent(op.f('ix_users_email'), 'users', ['email'], unique=True)
    create_index_if_absent(op.f('ix_users_id'), 'users', ['id'])


def downgrade() -> None:
    # Deja el downgrade tal cual (o ajusta si prefieres simetría exacta)
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.create_index('users_email_lower_uidx', 'users', [sa.text('lower(email)')], unique=False)
    op.create_unique_constraint('users_email_key', 'users', ['email'])

    # Skipping foreign key constraint drop due to naming issues
    # op.drop_constraint(None, 'user_roles', type_='foreignkey')
    # Skipping foreign key constraint creation due to existing constraint
    # op.create_foreign_key('user_roles_role_id_fkey', 'user_roles', 'roles', ['role_id'], ['id'])

    op.drop_index(op.f('ix_status_catalog_id'), table_name='status_catalog')
    op.drop_index(op.f('ix_status_catalog_code'), table_name='status_catalog')
    op.create_unique_constraint('status_catalog_code_key', 'status_catalog', ['code'])

    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.create_unique_constraint('roles_name_key', 'roles', ['name'])

    op.drop_index(op.f('ix_payment_events_source'), table_name='payment_events')
    op.drop_index(op.f('ix_payment_events_id'), table_name='payment_events')
    op.drop_index(op.f('ix_payment_events_event_id'), table_name='payment_events')
    op.create_unique_constraint('payment_events_event_id_key', 'payment_events', ['event_id'])
    op.create_index('idx_payment_events_donation_id_received_at', 'payment_events', ['donation_id', 'received_at'], unique=False)

    op.drop_index(op.f('ix_email_logs_type'), table_name='email_logs')
    op.drop_index(op.f('ix_email_logs_id'), table_name='email_logs')
    op.create_index('idx_email_logs_donation_id_statusid', 'email_logs', ['donation_id', 'status_id'], unique=False)

    op.drop_index(op.f('ix_donor_contacts_contact_preference'), table_name='donor_contacts')
    op.drop_index(op.f('ix_donations_id'), table_name='donations')
    op.create_index('idx_donations_statusid_created_at', 'donations', ['status_id', 'created_at'], unique=False)
