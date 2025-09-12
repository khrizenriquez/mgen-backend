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

```bash
# Instalar dependencias localmente
pip install -r requirements.txt

# Ejecutar migraciones
alembic upgrade head

# Desarrollo local (sin Docker)
uvicorn app.main:app --reload --port 8000
```

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

### Variables de Entorno

Crea un archivo `.env` desde la plantilla para personalizar configuraciones:

```bash
cp env.example .env
```

Variables importantes de pgAdmin:
```bash
# Configuración de pgAdmin (compatible con Windows/macOS/Linux)
PGADMIN_DEFAULT_EMAIL=admin@duku.dev
PGADMIN_DEFAULT_PASSWORD=admin123
```

> **Importante**: Se usa formato de email completo (`admin@duku.dev`) para evitar errores de validación en Windows. En sistemas Unix `admin@local` también funciona, pero `admin@duku.dev` garantiza compatibilidad universal.

## 📊 Monitoreo y Observabilidad

El sistema incluye un stack completo de observabilidad:

- **Grafana** (`http://localhost:3000`): Dashboards y visualizaciones
- **Prometheus** (`http://localhost:9090`): Recolección de métricas
- **Loki** (`http://localhost:3100`): Agregación de logs
- **Promtail**: Recolector de logs de contenedores

### Recursos de Sistema

**Uso de RAM**: ~857 MB total
- pgAdmin: 239 MB (desarrollo)
- RabbitMQ: 143 MB
- Grafana: 117 MB
- Loki: 104 MB
- API Backend: 84 MB
- PostgreSQL: 26 MB
- Frontend: 8 MB

**Uso de Disco**: ~3.4 GB (core) + ~2.2 GB (cache reclaimable)

## 🏗️ Arquitectura

- **Hexagonal Architecture** (Ports & Adapters)
- **FastAPI** con async/await
- **SQLAlchemy** ORM + **Alembic** migrations
- **PostgreSQL** database
- **RabbitMQ** messaging
- **Prometheus** + **Grafana** + **Loki** monitoring stack