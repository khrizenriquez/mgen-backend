"""
Configuración global de pytest para el proyecto.
Contiene fixtures compartidas y configuración de testing.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.infrastructure.database.database import get_database_session
from app.infrastructure.database.models import Base


# ===============================
# Database Testing Configuration
# ===============================

# URL de base de datos en memoria para tests
TEST_DATABASE_URL = "sqlite:///:memory:"

# Engine para tests con SQLite en memoria
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_database_session():
    """Override para usar base de datos de test."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override de la dependencia de base de datos
app.dependency_overrides[get_database_session] = override_get_database_session


# ===============================
# Pytest Configuration
# ===============================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """
    Fixture que proporciona una sesión de base de datos limpia para cada test.
    Crea todas las tablas al inicio y las limpia al final.
    """
    # Crear todas las tablas
    Base.metadata.create_all(bind=test_engine)
    
    # Crear sesión
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Limpiar todas las tablas después del test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture que proporciona un cliente HTTP async para testing de la API.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
def client() -> Generator[AsyncClient, None, None]:
    """
    Fixture sincrónico que proporciona un cliente HTTP para tests no-async.
    """
    with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ===============================
# Data Fixtures
# ===============================

@pytest.fixture
def sample_donation_data():
    """Datos de muestra para crear una donación."""
    return {
        "amount_gtq": 100.00,
        "donor_email": "test@example.com",
        "donor_name": "Test Donor",
        "donor_nit": "12345678",
        "reference_code": "TEST-REF-001",
        "correlation_id": "TEST-CORR-001"
    }


@pytest.fixture
def sample_user_data():
    """Datos de muestra para crear un usuario."""
    return {
        "email": "testuser@example.com",
        "password": "testpassword123",
        "is_active": True,
        "email_verified": False
    }


# ===============================
# Utility Functions for Tests
# ===============================

def pytest_configure(config):
    """Configuración inicial de pytest."""
    # Marcadores personalizados
    config.addinivalue_line(
        "markers", "unit: tests unitarios rápidos"
    )
    config.addinivalue_line(
        "markers", "integration: tests de integración"
    )
    config.addinivalue_line(
        "markers", "slow: tests lentos que pueden ser omitidos"
    )


def pytest_collection_modifyitems(config, items):
    """Modificar items de tests collectados."""
    # Agregar marcador 'unit' por defecto si no tiene ninguno
    for item in items:
        if not any(marker.name in ['unit', 'integration', 'slow'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)

