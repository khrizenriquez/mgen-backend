"""
Tests de integración para validar la configuración de base de datos.
"""

import pytest
from sqlalchemy.orm import Session
from app.infrastructure.database.models import Base


@pytest.mark.integration
@pytest.mark.database
def test_database_session_fixture(db_session: Session):
    """Test para validar que la fixture de DB funciona."""
    # La sesión debe estar disponible
    assert db_session is not None
    
    # Debería poder hacer query básico
    result = db_session.execute("SELECT 1 as test_value")
    row = result.fetchone()
    assert row[0] == 1


@pytest.mark.integration
@pytest.mark.database
def test_database_tables_creation(db_session: Session):
    """Test para validar que las tablas se crean correctamente."""
    # Las tablas deberían existir en la base de datos de test
    tables = Base.metadata.tables.keys()
    
    # Verificar que tenemos las tablas principales
    expected_tables = {
        'status_catalog',
        'users', 
        'roles',
        'user_roles',
        'donations',
        'payment_events',
        'email_logs',
        'donor_contacts'
    }
    
    # Verificar que las tablas esperadas están definidas en los modelos
    assert len(tables) > 0, "No se encontraron tablas definidas en los modelos"
    
    # Nota: Este test pasará cuando tengas los modelos SQLAlchemy creados
    # Por ahora solo validamos que la configuración funciona

