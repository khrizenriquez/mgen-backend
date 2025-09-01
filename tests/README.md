# Tests - Sistema de Donaciones Backend

Documentación completa del sistema de testing configurado con pytest.

## 🚀 Configuración

### Dependencias de Testing
```txt
pytest==7.4.3          # Framework de testing
pytest-asyncio==0.21.1 # Soporte para tests async
httpx==0.25.2          # Cliente HTTP para testing FastAPI
```

### Estructura de Directorios
```
tests/
├── __init__.py
├── conftest.py              # Configuración global y fixtures
├── unit/                    # Tests unitarios
│   ├── __init__.py
│   ├── adapters/           # Tests de controladores y schemas
│   ├── domain/             # Tests de entidades y servicios
│   └── infrastructure/     # Tests de DB y external
└── integration/            # Tests de integración
    ├── __init__.py
    ├── adapters/
    ├── domain/
    └── infrastructure/
```

## 🧪 Ejecutar Tests

### Comandos Básicos
```bash
# Ejecutar todos los tests
pytest

# Tests unitarios únicamente
pytest -m unit

# Tests de integración únicamente  
pytest -m integration

# Tests de API únicamente
pytest -m api

# Tests con output verbose
pytest -v

# Tests específicos por archivo
pytest tests/unit/test_health.py

# Tests específicos por función
pytest tests/unit/test_health.py::test_health_endpoint
```

### Comandos Avanzados
```bash
# Ejecutar con cobertura
pytest --cov=app --cov-report=html

# Saltear tests lentos
pytest -m "not slow"

# Solo tests que fallan
pytest --lf

# Detener en el primer fallo
pytest -x

# Ejecutar tests en paralelo (requiere pytest-xdist)
pytest -n auto
```

## 🔧 Fixtures Disponibles

### Base de Datos
- `db_session`: Sesión de SQLAlchemy con base de datos en memoria
- Cada test obtiene una DB limpia (tables created/dropped)

### Cliente HTTP
- `async_client`: Cliente async para tests de API
- `client`: Cliente sincrónico para tests simples

### Datos de Muestra
- `sample_donation_data`: Datos de donación para tests
- `sample_user_data`: Datos de usuario para tests

## 🏷️ Marcadores Disponibles

### Por Tipo
- `@pytest.mark.unit`: Tests unitarios
- `@pytest.mark.integration`: Tests de integración
- `@pytest.mark.slow`: Tests lentos (pueden omitirse)

### Por Componente
- `@pytest.mark.api`: Tests de endpoints
- `@pytest.mark.database`: Tests de base de datos
- `@pytest.mark.external`: Tests de servicios externos

### Ejemplo de Uso
```python
@pytest.mark.unit
@pytest.mark.api
async def test_create_donation(async_client, sample_donation_data):
    response = await async_client.post("/donations", json=sample_donation_data)
    assert response.status_code == 201
```

## 📋 Configuración (pytest.ini)

- **Autodiscovery**: Encuentra automáticamente tests en `/tests`
- **Patrones**: `test_*.py`, `*_test.py`
- **Asyncio**: Soporte automático para tests async
- **Markers**: Marcadores estrictos (deben estar definidos)
- **Output**: Verbose con colores

## 🎯 Ejemplos de Tests

### Test Unitario Simple
```python
@pytest.mark.unit
def test_donation_amount_validation(sample_donation_data):
    # Test de validación de lógica de negocio
    assert sample_donation_data["amount_gtq"] > 0
```

### Test de API
```python
@pytest.mark.unit
@pytest.mark.api
async def test_health_endpoint(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Test de Base de Datos
```python
@pytest.mark.integration
@pytest.mark.database
def test_create_donation(db_session, sample_donation_data):
    # Test de creación en base de datos
    donation = Donation(**sample_donation_data)
    db_session.add(donation)
    db_session.commit()
    assert donation.id is not None
```

## ⚙️ Configuración de IDE

### VS Code
Agregar a `.vscode/settings.json`:
```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.unittestEnabled": false
}
```

### PyCharm
1. File > Settings > Tools > Python Integrated Tools
2. Testing > Default test runner: pytest
3. Pytest target: Custom > tests

## 🔍 Debugging Tests

```bash
# Ejecutar con debugger
pytest --pdb

# Debugging específico
pytest --pdb tests/unit/test_health.py::test_health_endpoint

# Output completo sin truncar
pytest -s --tb=long
```

## 📊 Coverage Report

```bash
# Generar reporte de cobertura
pytest --cov=app --cov-report=html

# Ver reporte en navegador
open htmlcov/index.html
```

## 🚨 Troubleshooting

### Error: "ModuleNotFoundError"
- Verificar que estás en el directorio del proyecto
- Verificar que `__init__.py` existe en tests/

### Error: "Database tables not found"  
- Los modelos SQLAlchemy deben estar importados en conftest.py
- Base.metadata debe contener todas las tablas

### Tests lentos
- Usar marcador `@pytest.mark.slow`
- Ejecutar sin tests lentos: `pytest -m "not slow"`

---

**Configuración completa y lista para usar.** 🎉

