# Sistema de Migraciones con Alembic

## Descripción General

Este proyecto utiliza **Alembic** para gestionar las migraciones de base de datos de manera versionada y controlada. Alembic es la herramienta oficial de migraciones para SQLAlchemy.

## Configuración

### Archivos de Configuración

- **`alembic.ini`**: Configuración principal de Alembic
- **`alembic/env.py`**: Entorno de migración y configuración de metadatos
- **`alembic/versions/`**: Directorio que contiene todas las migraciones

### Configuración de Base de Datos

```ini
# alembic.ini
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/donations_db
```

## Comandos Principales

### Usando el Script de Migración

```bash
# Ejecutar todas las migraciones pendientes
./scripts/migrate.sh upgrade

# Crear nueva migración
./scripts/migrate.sh revision "Descripción de la migración"

# Ver estado actual
./scripts/migrate.sh current

# Ver historial
./scripts/migrate.sh history

# Revertir última migración
./scripts/migrate.sh downgrade -1
```

### Comandos Directos de Alembic

```bash
# Ejecutar migraciones
docker-compose exec api alembic upgrade head

# Crear migración
docker-compose exec api alembic revision --autogenerate -m "Descripción"

# Ver estado
docker-compose exec api alembic current

# Ver historial
docker-compose exec api alembic history
```

## Estructura de Migraciones

### Formato de Archivos

```
alembic/versions/
├── 4a9d440c02ab_initial_migration_create_all_tables.py
├── 47c7306d848e_create_missing_tables_and_indexes.py
└── ...
```

### Estructura de una Migración

```python
"""Descripción de la migración

Revision ID: 47c7306d848e
Revises: 4a9d440c02ab
Create Date: 2025-09-02 01:03:10.210841

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '47c7306d848e'
down_revision = '4a9d440c02ab'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Comandos de migración hacia adelante
    pass

def downgrade() -> None:
    # Comandos de reversión
    pass
```

## Flujo de Trabajo

### 1. Crear Nueva Migración

```bash
# Después de modificar los modelos SQLAlchemy
./scripts/migrate.sh revision "Agregar nueva tabla usuarios"
```

### 2. Revisar la Migración Generada

```bash
# Revisar el archivo generado en alembic/versions/
# Ajustar si es necesario
```

### 3. Ejecutar la Migración

```bash
# En desarrollo
./scripts/migrate.sh upgrade

# En producción (después de revisar)
docker-compose exec api alembic upgrade head
```

### 4. Verificar el Estado

```bash
./scripts/migrate.sh current
./scripts/migrate.sh history
```

## Buenas Prácticas

### 1. Nombres Descriptivos

```bash
# ✅ Bueno
./scripts/migrate.sh revision "Agregar campo email a usuarios"

# ❌ Malo
./scripts/migrate.sh revision "fix"
```

### 2. Revisar Migraciones Generadas

- Siempre revisa las migraciones autogeneradas
- Ajusta los tipos de datos si es necesario
- Comenta operaciones problemáticas

### 3. Testing

```bash
# Ejecutar migraciones en entorno de desarrollo
./scripts/migrate.sh upgrade

# Verificar que la aplicación funcione
docker-compose exec api python -m pytest tests/
```

### 4. Rollback

```bash
# Revertir última migración
./scripts/migrate.sh downgrade -1

# Revertir a revisión específica
./scripts/migrate.sh downgrade 4a9d440c02ab
```

## Solución de Problemas

### Error: Column Used by View

Si encuentras errores como:
```
cannot alter type of a column used by a view or rule
```

**Solución**: Comenta la operación problemática en la migración:

```python
def upgrade() -> None:
    # Skipping payload_raw type change due to view dependencies
    # op.alter_column('payment_events', 'payload_raw', ...)
    pass
```

### Error: Identity Column

Si encuentras errores como:
```
column "id" of relation "roles" is an identity column
```

**Solución**: Comenta la modificación de columna de identidad:

```python
def upgrade() -> None:
    # Skipping identity column modification
    # op.alter_column('roles', 'id', ...)
    pass
```

### Verificar Estado de la Base de Datos

```bash
# Ver tablas existentes
docker-compose exec db psql -U postgres -d donations_db -c "\dt"

# Ver vistas existentes
docker-compose exec db psql -U postgres -d donations_db -c "\dv"

# Ver estructura de tabla específica
docker-compose exec db psql -U postgres -d donations_db -c "\d+ nombre_tabla"
```

## Migraciones Existentes

### Migración Inicial (4a9d440c02ab)
- **Descripción**: Migración inicial para crear todas las tablas
- **Estado**: Marcada como fallida (problemas con vistas)

### Crear Tablas e Índices (47c7306d848e)
- **Descripción**: Crear tablas faltantes e índices
- **Estado**: ✅ Completada exitosamente
- **Incluye**: 
  - Índices para todas las tablas
  - Constraints de foreign keys
  - Constraints únicos

## Integración con CI/CD

### Verificación Automática

```yaml
# .github/workflows/migrations.yml
- name: Verify migrations
  run: |
    docker-compose exec api alembic current
    docker-compose exec api alembic history
```

### Pre-deployment

```bash
# Antes de desplegar
./scripts/migrate.sh current
./scripts/migrate.sh upgrade
```

## Recursos Adicionales

- [Documentación Oficial de Alembic](https://alembic.sqlalchemy.org/)
- [Guía de Migraciones de SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/migrations.html)
- [PostgreSQL Identity Columns](https://www.postgresql.org/docs/current/ddl-generated-columns.html)
