# mgen-backend

Sistema de gestión de donaciones - 

## 🚀 Inicio Rápido

### Prerrequisitos
- Docker y Docker Compose instalados
- Git

### Levantar los contenedores

```bash
# Clonar el repositorio
git clone <repository-url>
cd mgen-backend

# Levantar todos los servicios
docker-compose up -d

# Ver logs de los servicios
docker-compose logs -f

# Detener los servicios
docker-compose down
```

## 🪟 Configuración para Windows (Desarrollo Local)

### Prerrequisitos Windows

1. **Python 3.11-3.13**
   - Descargar desde: https://python.org/downloads/
   - Durante instalación: ☑️ "Add Python to PATH"
   - Verificar: `python --version` en PowerShell

2. **PostgreSQL**
   - Descargar desde: https://postgresql.org/download/windows/
   - Durante instalación, recordar usuario/contraseña
   - Verificar: `psql --version` en PowerShell

3. **Git** (opcional si ya tienes)
   - Descargar desde: https://git-scm.com/download/win

### Opción 1: Entorno Virtual (venv) - Recomendado

```powershell
# 1. Clonar el repositorio
git clone <repository-url>
cd mgen-backend

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual (PowerShell)
.\venv\Scripts\activate

# 4. Actualizar pip
python -m pip install --upgrade pip

# 5. Instalar dependencias
# ⚠️ Si tienes problemas con psycopg2-binary en Windows ARM64/Python 3.13:
pip install -r requirements-dev.txt  # Para Windows con problemas de compatibilidad
# ✅ Para otros casos (Docker, Linux, macOS):
pip install -r requirements.txt      # Archivo oficial

# 6. Configurar variables de entorno
# Crear archivo .env basado en env.example
copy env.example .env
# Editar .env con tus credenciales de PostgreSQL
# IMPORTANTE: La app cargará automáticamente las variables del .env

# 7. Ejecutar migraciones
alembic upgrade head
# Si da error "tabla ya existe", ejecutar: alembic stamp head

# 8. Levantar la aplicación
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Opción 2: Conda Environment

```powershell
# 1. Clonar el repositorio
git clone <repository-url>
cd mgen-backend

# 2. Crear ambiente conda
conda create -n mgen-backend python=3.11
conda activate mgen-backend

# 3. Instalar dependencias
# ⚠️ Si tienes problemas con psycopg2-binary en Windows ARM64/Python 3.13:
pip install -r requirements-dev.txt  # Para Windows con problemas de compatibilidad
# ✅ Para otros casos:
pip install -r requirements.txt      # Archivo oficial

# 4. Configurar variables de entorno
copy env.example .env
# Editar .env con tus credenciales

# 5. Ejecutar migraciones
alembic upgrade head

# 6. Levantar la aplicación
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Problemas Comunes en Windows

### Problemas Comunes en Windows

#### ❌ Error: No se pueden instalar dependencias (Python 3.13 + ARM64)
```powershell
# Síntoma
ERROR: Microsoft Visual C++ 14.0 or greater is required

# Solución: Usar archivo específico para Windows
pip install -r requirements-dev.txt
```

#### ❌ PostgreSQL no se conecta
```powershell
# Verificar si PostgreSQL está corriendo
python -c "import socket; s = socket.socket(); print('PostgreSQL OK' if s.connect_ex(('localhost', 5432)) == 0 else 'PostgreSQL no accesible'); s.close()"

# Si no está corriendo, iniciar PostgreSQL (Windows Service)
Start-Service postgresql-x64-15  # Ajustar versión según instalación
```

#### ❌ Error en migraciones: "tabla ya existe"
```powershell
# Síntoma
ProgrammingError: la relación «status_catalog» ya existe

# Solución: Sincronizar Alembic con tablas existentes
alembic stamp head
```

### Archivos de dependencias

| Archivo | Uso | Descripción |
|---------|-----|-------------|
| `requirements.txt` | **Oficial** | Docker, Linux, macOS, Producción, CI/CD |
| `requirements-dev.txt` | **Windows local** | Solo para desarrollo en Windows con problemas de compatibilidad |

### Configuración de .env para Windows

```env
# Database Configuration
DATABASE_URL=postgresql+pg8000://postgres:TU_PASSWORD@localhost:5432/donations_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=TU_PASSWORD
POSTGRES_DB=donations_db

# Database Pool Configuration (opcional)
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
SQL_ECHO=false

# Application Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### Comandos útiles para desarrollo

```powershell
# Activar entorno virtual
.\venv\Scripts\activate

# Desactivar entorno virtual
deactivate

# Ver paquetes instalados
pip list

# Actualizar requirements.txt
pip freeze > requirements.txt

# Ejecutar tests
pytest

# Ver logs de la aplicación
# Los logs aparecerán en la consola al ejecutar uvicorn
```

### URLs de desarrollo local

Una vez levantada la aplicación:
- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 🐍 Comparación: venv vs Conda

| Característica | venv | Conda |
|---------------|------|-------|
| **Incluido con Python** | ✅ Sí | ❌ Instalación separada |
| **Gestión de dependencias** | pip solamente | pip + conda |
| **Paquetes binarios** | Limitado | Excelente |
| **Peso** | Ligero (~5-10 MB) | Pesado (~500 MB-3 GB) |
| **Velocidad** | Rápido | Más lento |
| **Gestión de versiones Python** | ❌ No | ✅ Sí |
| **Recomendado para** | Proyectos Python simples | Data Science, ML |

#### ¿Cuándo usar cada uno?

**Usar venv si:**
- Es tu primer proyecto Python
- Solo usas paquetes de PyPI
- Prefieres herramientas simples
- Espacio limitado en disco

**Usar conda si:**
- Trabajas con data science/ML
- Necesitas paquetes científicos (numpy, pandas, etc.)
- Trabajas con múltiples versiones de Python
- Ya tienes Anaconda instalado

## 📊 Servicios y Puertos

| Servicio | Puerto | URL | Descripción |
|----------|---------|-----|-------------|
| **API** | `8000` | http://localhost:8000 | FastAPI Backend |
| **PostgreSQL** | `5432` | localhost:5432 | Base de datos |
| **RabbitMQ Management** | `15672` | http://localhost:15672 | UI de gestión (guest/guest) |
| **RabbitMQ AMQP** | `5672` | localhost:5672 | Broker de mensajes |
| **Prometheus** | `9090` | http://localhost:9090 | Métricas |
| **Grafana** | `3000` | http://localhost:3000 | Dashboards (admin/admin) |
| **pgAdmin** | `5050` | http://localhost:5050 | Admin Postgres (admin@duku.dev/admin123) |

## 🔐 Credenciales por defecto

- **PostgreSQL**: `postgres / postgres` (definidas en `docker-compose.yml`)
- **RabbitMQ (UI)**: `guest / guest` (Management en `http://localhost:15672`)
- **Grafana**: `admin / admin` (cambiables vía variables `GF_SECURITY_ADMIN_*`)
- **Prometheus**: sin autenticación por defecto (`http://localhost:9090`)
- **pgAdmin**: `admin@duku.dev / admin123` (configurable via `.env`)

Nota: Cambia estas credenciales en producción mediante variables de entorno o secrets.

## 🔗 Enlaces Útiles

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **API Redoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

## 🛠️ Desarrollo

> **💡 Nota**: Para desarrollo en Windows, consulta la sección [Configuración para Windows](#-configuración-para-windows-desarrollo-local) arriba.

```bash
# Instalar dependencias localmente
pip install -r requirements.txt

# Ejecutar migraciones
alembic upgrade head

# Desarrollo local (sin Docker)
uvicorn app.main:app --reload --port 8000
```

### Dependencias por plataforma

- **Linux/macOS + Docker**: Usa `requirements.txt` original con `psycopg2-binary`
- **Windows (desarrollo local)**: Usa `requirements.txt` modificado con `pg8000`
- **Python 3.13 + ARM64**: Requiere `pg8000` por compatibilidad

### Herramientas locales

#### Acceso a pgAdmin (Desarrollo Local)

**URL**: http://localhost:5050
- **Email**: `admin@duku.dev`
- **Password**: `admin123`

> **Nota sobre compatibilidad**: Se usa `admin@duku.dev` en lugar de `admin@local` para compatibilidad entre Windows, macOS y Linux. pgAdmin en Windows requiere formato de email válido con TLD.

#### Configuración de conexión PostgreSQL en pgAdmin

Para conectar pgAdmin al servidor PostgreSQL dentro de Docker:

```
General Tab:
└── Name: Donations Database Server

Connection Tab:
├── Host name/address: db                    # Nombre del servicio Docker
├── Port: 5432
├── Maintenance database: postgres
├── Username: postgres                       # Usuario de desarrollo
├── Password: postgres                       # Contraseña de desarrollo
└── Save password: ✅ (recomendado)
```

**Nota**: Estos son valores de desarrollo. En producción las credenciales se gestionarán via secrets (Railway/Render).

## 🏗️ Arquitectura

- **Hexagonal Architecture** (Ports & Adapters)
- **FastAPI** con async/await
- **SQLAlchemy** ORM + **Alembic** migrations
- **PostgreSQL** database
- **RabbitMQ** messaging
- **Prometheus** + **Grafana** monitoring