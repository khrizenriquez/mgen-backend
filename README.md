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

Acceso a pgAdmin:

```
http://localhost:5050
Email: admin@duku.dev
Password: admin123
```

## 🏗️ Arquitectura

- **Hexagonal Architecture** (Ports & Adapters)
- **FastAPI** con async/await
- **SQLAlchemy** ORM + **Alembic** migrations
- **PostgreSQL** database
- **RabbitMQ** messaging
- **Prometheus** + **Grafana** monitoring