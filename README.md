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

### Validación de Configuración

La aplicación incluye un script automático de validación que verifica que todas las variables críticas estén configuradas correctamente:

```bash
# Ejecutar validación manualmente
python scripts/validate_config.py
```

**La validación se ejecuta automáticamente al iniciar la aplicación.**

### Validación de Seguridad

Además de la validación de configuración, incluye un script de pruebas de seguridad:

```bash
# Ejecutar pruebas de seguridad
python scripts/security_test.py
```

Este script valida:
- ✅ Restricciones de creación de usuarios por roles
- ✅ Protección de endpoints que requieren autenticación
- ✅ Prevención de escalada de privilegios

### 🔐 Características de Seguridad Implementadas

- **Autenticación JWT** completa con access y refresh tokens
- **Control de acceso basado en roles** (ADMIN, ORGANIZATION, AUDITOR, DONOR, USER)
- **Validación de roles** en creación de usuarios para prevenir escalada de privilegios
- **Rate limiting** básico (10 requests/minuto)
- **Protección automática** de endpoints sensibles
- **Validación de configuración** al inicio
- **Scripts de pruebas de seguridad** automatizadas

### Variables de Entorno Requeridas

Antes de ejecutar la aplicación, configura las siguientes variables de entorno críticas para seguridad:

```bash
# JWT Secret (REQUERIDO - sin valor por defecto)
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here

# Rate Limiting
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60

# Email Configuration (Mailjet - requerido para producción)
MAILJET_API_KEY=your-mailjet-api-key
MAILJET_API_SECRET=your-mailjet-api-secret
FROM_EMAIL=noreply@donacionesgt.org
FROM_NAME=Sistema de Donaciones
FRONTEND_URL=http://localhost:3000

# Default User Password (solo para desarrollo)
DEFAULT_USER_PASSWORD=seminario123
```

**⚠️ IMPORTANTE**: Sin `JWT_SECRET_KEY` configurada, la aplicación no iniciará.

### Usuarios de Prueba Automáticos

Al levantar los contenedores por primera vez, se crearán automáticamente **3 usuarios de prueba**:

| Email | Password | Rol | Descripción |
|-------|----------|-----|-------------|
| `adminseminario@test.com` | `seminario123` | ADMIN | Administrador del sistema |
| `donorseminario@test.com` | `seminario123` | DONOR | Usuario donante registrado |
| `userseminario@test.com` | `seminario123` | USER | Usuario regular (puede actualizarse a DONOR) |

**Nota**: Los usuarios se crean solo en modo desarrollo (`ENVIRONMENT=development`).

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

## 🔐 Autenticación y Roles

El sistema implementa autenticación JWT completa con control de acceso basado en roles y soporte para múltiples organizaciones.

### Jerarquía de Roles del Sistema

| Rol | Nivel | Descripción | Permisos |
|-----|-------|-------------|----------|
| **ADMIN** | 🔴 Máximo | Administrador del sistema | ✅ **Acceso completo** a todas las organizaciones y datos<br>✅ Gestionar usuarios y roles<br>✅ Ver todas las estadísticas globales |
| **ORGANIZATION** | 🟠 Alto | Administrador de ONG | ✅ Gestionar su propia organización<br>✅ Ver donaciones de su ONG<br>✅ Gestionar usuarios de su ONG<br>❌ No ve datos de otras ONGs |
| **AUDITOR** | 🟡 Medio | Auditor/Compliance | ✅ **Solo lectura** de toda la información<br>✅ Ver estadísticas y reportes<br>❌ No puede modificar datos |
| **DONOR** | 🟢 Bajo | Donante registrado | ✅ Ver sus propias donaciones<br>✅ Gestionar su perfil<br>✅ Realizar donaciones |
| **USER** | 🔵 Mínimo | Usuario regular | ✅ Acceso básico al sistema<br>✅ Gestionar su perfil<br>❌ Acceso limitado a datos |

### 🏢 Arquitectura Multi-ONG

El sistema está preparado para manejar múltiples organizaciones de manera escalable:

#### **Organización por Defecto**
- **ID**: `550e8400-e29b-41d4-a716-446655440000`
- **Nombre**: Fundación Donaciones Guatemala
- **Estado**: Activa por defecto

#### **Características Multi-ONG**
- ✅ **Aislamiento de datos**: Cada organización ve solo sus propios datos
- ✅ **Control administrativo**: Los admins de organización gestionan su entidad
- ✅ **Escalabilidad**: Fácil agregar nuevas ONGs sin afectar existentes
- ✅ **Auditoría global**: Auditores pueden ver datos de todas las organizaciones
- ✅ **Flexibilidad**: Un usuario puede cambiar de organización (gestionado por admin)

#### **Asignación de Usuarios a Organizaciones**
- Los nuevos usuarios se registran sin organización asignada
- Los administradores asignan usuarios a organizaciones según corresponda
- Los usuarios ORGANIZATION solo pueden gestionar usuarios de su propia organización
- Los usuarios ADMIN pueden gestionar usuarios de cualquier organización

#### **Endpoints de Organizaciones (Admin Only)**
```http
# Gestión de Organizaciones
GET  /api/v1/organizations           # Listar todas las organizaciones
POST /api/v1/organizations           # Crear nueva organización
GET  /api/v1/organizations/{id}      # Ver organización específica
PUT  /api/v1/organizations/{id}      # Actualizar organización
DELETE /api/v1/organizations/{id}    # Eliminar organización

# Estadísticas por Organización
GET  /api/v1/organizations/summary/all    # Resumen de todas las organizaciones
GET  /api/v1/organizations/{id}/summary   # Resumen de organización específica
```

### Endpoints de Autenticación

#### Públicos (sin autenticación requerida)
```http
POST /api/v1/auth/register          # Registro de nuevos usuarios
POST /api/v1/auth/login             # Inicio de sesión
POST /api/v1/auth/forgot-password   # Solicitar reset de contraseña
POST /api/v1/auth/reset-password    # Reset de contraseña con token
POST /api/v1/auth/verify-email      # Verificar email con token
```

#### Protegidos (requieren JWT Bearer token)
```http
GET  /api/v1/auth/dashboard         # Dashboard personalizado por rol
GET  /api/v1/auth/me                # Información del usuario actual
POST /api/v1/auth/change-password   # Cambiar contraseña
POST /api/v1/auth/logout            # Cerrar sesión
POST /api/v1/auth/refresh           # Refresh token de acceso

# Solo ADMIN
GET  /api/v1/auth/admin/users       # Lista de todos los usuarios
```

### Control de Acceso en Endpoints Existentes

#### Usuarios (`/api/v1/users`)
- `GET /users` - **ADMIN/ORGANIZATION**: Lista de usuarios (filtrada por organización para ORGANIZATION)
- `GET /users/{id}` - **Usuario autenticado**: Solo puede ver su propio perfil (o ADMIN/ORGANIZATION ve perfiles de su organización)
- `PUT /users/{id}` - **Usuario autenticado**: Solo puede actualizar su propio perfil (o ADMIN/ORGANIZATION actualiza perfiles de su organización)
- `DELETE /users/{id}` - **ADMIN/ORGANIZATION**: Eliminar usuarios de su organización (solo ADMIN puede eliminar de cualquier organización)
- `POST /users` - **Público**: Crear nuevo usuario (registro)

#### Donaciones (`/api/v1/donations`)
- `GET /donations` - **Usuario autenticado**:
  - **ADMIN**: Ve todas las donaciones del sistema
  - **ORGANIZATION**: Ve donaciones de su organización
  - **AUDITOR**: Ve todas las donaciones (solo lectura)
  - **DONOR**: Ve solo sus propias donaciones
  - **USER**: Sin acceso (lista vacía)
- `GET /donations/stats` - **Usuario autenticado**:
  - **ADMIN**: Estadísticas globales del sistema
  - **ORGANIZATION**: Estadísticas de su organización
  - **AUDITOR**: Estadísticas globales (solo lectura)
  - **DONOR**: Estadísticas de sus propias donaciones
  - **USER**: Sin acceso (estadísticas en cero)

### Uso de JWT Tokens

#### Obtener Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

#### Usar Token en Requests
```bash
curl -X GET "http://localhost:8000/api/v1/auth/dashboard" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

#### Refresh Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN_HERE"}'
```

### Variables de Entorno para JWT

```env
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Configuration (para forgot password)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FRONTEND_URL=http://localhost:3000
```

## 🚀 Despliegue en Producción

### Backend - Railway

El backend está configurado para desplegarse automáticamente en Railway:

1. **Conexión del Repositorio**: Conecta tu repositorio de GitHub a Railway
2. **Variables de Entorno**: Configura los secrets en Railway:
   - `JWT_SECRET_KEY`: Clave secreta para JWT (genera una segura)
   - `DATABASE_URL`: Proporcionada automáticamente por Railway
   - `SMTP_*`: Configuración de email para notificaciones
   - `FRONTEND_URL`: URL de tu frontend en Netlify

3. **Despliegue Automático**: Cada push a `main` activa el CI/CD y despliega automáticamente

### Frontend - Netlify

Para el frontend (repositorio separado):

1. **Conectar Repositorio**: Conecta el repo del frontend a Netlify
2. **Variables de Entorno**:
   - `VITE_API_URL`: URL del backend en Railway
   - `VITE_APP_ENV`: "production"

3. **Build Settings**:
   - Build command: `npm run build`
   - Publish directory: `dist`

### CI/CD con GitHub Actions

El proyecto incluye pipelines automatizados:

- **Tests**: Ejecuta tests y coverage en cada PR
- **Build**: Construye imagen Docker y sube a GitHub Container Registry
- **Deploy**: Despliega automáticamente a Railway en pushes a `main`

### Secrets Requeridos

#### GitHub Secrets (para CI/CD):
- `RAILWAY_API_TOKEN`: Token de API de Railway
- `RAILWAY_ENVIRONMENT_ID`: ID del environment de producción

#### Railway Secrets:
- `JWT_SECRET_KEY`: Clave segura para tokens JWT
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`: Configuración email
- `FRONTEND_URL`: URL del frontend en producción

#### Netlify Secrets:
- `VITE_API_URL`: URL del backend desplegado

## 🏗️ Arquitectura

- **Hexagonal Architecture** (Ports & Adapters)
- **FastAPI** con async/await
- **SQLAlchemy** ORM + **Alembic** migrations
- **PostgreSQL** database
- **RabbitMQ** messaging
- **Prometheus** + **Grafana** monitoring
- **JWT Authentication** con control de acceso basado en roles