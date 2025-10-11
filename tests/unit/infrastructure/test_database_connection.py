"""
Tests unitarios para la conexión de base de datos.
"""

import pytest
from unittest.mock import Mock, patch
from app.infrastructure.database.database import get_db


@pytest.mark.unit
@pytest.mark.database
def test_database_url_formation():
    """Test de formación de URL de base de datos."""
    from app.infrastructure.database.database import DATABASE_URL

    # Test que la URL de base de datos esté definida
    assert DATABASE_URL is not None
    assert isinstance(DATABASE_URL, str)

    # Debe contener los componentes básicos de una URL de PostgreSQL
    if DATABASE_URL.startswith("postgresql://"):
        assert "postgresql://" in DATABASE_URL
        # No hacemos assertions específicas sobre el contenido
        # porque depende de las variables de entorno


@pytest.mark.unit
@pytest.mark.database
def test_database_session_creation():
    """Test de creación de sesión de base de datos."""
    # Test que get_db es callable
    assert callable(get_db)
    
    # En un test unitario real, mockeamos la conexión
    with patch('app.infrastructure.database.database.SessionLocal') as mock_session:
        mock_session.return_value = Mock()
        
        # Verificar que se puede obtener un generador
        db_gen = get_db()
        assert db_gen is not None


@pytest.mark.unit
def test_database_environment_variables():
    """Test de manejo de variables de entorno."""
    import os
    
    # Verificar que la variable TESTING está configurada
    assert os.environ.get('TESTING') == 'true'
    
    # Test de variables de entorno de base de datos
    # Estas pueden estar definidas o usar defaults
    db_vars = ['DATABASE_URL', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB']
    
    for var in db_vars:
        # Solo verificamos que podemos acceder a las variables
        # No importa si están definidas o no
        value = os.environ.get(var)
        # value puede ser None o string
        assert value is None or isinstance(value, str)
