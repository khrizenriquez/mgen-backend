# 🐧 WSL DEVELOPMENT SETUP

## ✅ VENTAJAS DE WSL
- Ambiente Linux nativo (compatible con el proyecto)
- PostgreSQL nativo de Linux
- Mejor compatibilidad con el stack Python/FastAPI
- Sin problemas de rutas Windows vs Linux

## 🛠️ PRERREQUISITOS WSL

### 1. Verificar WSL Setup
```bash
# Verificar versión de WSL
wsl --version

# Verificar distribución
cat /etc/os-release
# Recomendado: Ubuntu 20.04+ o 22.04
```

### 2. Actualizar Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

## 🚀 SETUP PASO A PASO

### Paso 1: Instalar Python 3.11+
```bash
# Instalar Python y herramientas
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# Verificar instalación
python3.11 --version

# Crear alias para facilidad
echo "alias python=python3.11" >> ~/.bashrc
echo "alias pip=pip3" >> ~/.bashrc
source ~/.bashrc
```

### Paso 2: Instalar PostgreSQL
```bash
# Instalar PostgreSQL
sudo apt install postgresql postgresql-contrib libpq-dev -y

# Iniciar servicio
sudo service postgresql start

# Configurar usuario
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"

# Crear base de datos
sudo -u postgres createdb donations_db

# Verificar conexión
psql -U postgres -h localhost -d donations_db -c "SELECT version();"
```

### Paso 3: Clonar y Setup Proyecto
```bash
# Clonar repositorio (si no está clonado)
cd ~
git clone <repo-url>
cd sistema-donaciones/mgen-backend

# Crear virtual environment
python -m venv venv

# Activar virtual environment
source venv/bin/activate

# Verificar que está activo
which python  # Debe mostrar ruta del venv
```

### Paso 4: Instalar Dependencias
```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalaciones críticas
python -c "import structlog; print('✅ structlog OK')"
python -c "import sqlalchemy; print('✅ SQLAlchemy OK')"
python -c "import alembic; print('✅ Alembic OK')"
python -c "import psycopg2; print('✅ psycopg2 OK')"
```

### Paso 5: Configurar Ambiente
```bash
# Crear archivo .env
cp env.example .env

# Editar .env con configuración WSL
nano .env
```

**Contenido del .env para WSL:**
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/donations_db
SERVICE_NAME=donations-api
VERSION=1.0.0
LOG_LEVEL=INFO
ENVIRONMENT=development
SQL_ECHO=false
```

## 🔧 SOLUCIÓN AL ERROR KeyError: '4a9d440c02ab'

### Diagnóstico en WSL
```bash
# 1. Activar venv (siempre primero)
source venv/bin/activate

# 2. Verificar archivos de migración
ls -la alembic/versions/

# 3. Ver estado de tabla alembic_version
psql -U postgres -h localhost -d donations_db -c "SELECT * FROM alembic_version;"

# 4. Ver historial de migraciones
alembic history --verbose
```

### Solución Específica WSL
```bash
# Paso 1: Limpiar estado inconsistente
psql -U postgres -h localhost -d donations_db -c "DELETE FROM alembic_version;"

# Paso 2: Verificar si tablas existen
psql -U postgres -h localhost -d donations_db -c "\dt"

# Paso 3a: Si las tablas YA existen
alembic stamp head

# Paso 3b: Si NO existen tablas, ejecutar schema
psql -U postgres -h localhost -d donations_db -f schema.sql
alembic stamp head

# Paso 4: Verificar que funciona
alembic current
alembic history
```

## 🚀 EJECUTAR LA APLICACIÓN

### Iniciar Servicios WSL
```bash
# Iniciar PostgreSQL (si no está corriendo)
sudo service postgresql start

# Verificar que está corriendo
sudo service postgresql status
```

### Ejecutar FastAPI
```bash
# Activar ambiente
source venv/bin/activate

# Ejecutar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Verificar que funciona
curl http://localhost:8000/health/
```

## 🐛 TROUBLESHOOTING WSL

### Error: "could not connect to server"
```bash
# Verificar PostgreSQL está corriendo
sudo service postgresql status

# Si no está corriendo
sudo service postgresql start

# Verificar puerto
netstat -an | grep 5432

# Verificar configuración PostgreSQL
sudo nano /etc/postgresql/*/main/postgresql.conf
# Buscar: listen_addresses = 'localhost'

sudo nano /etc/postgresql/*/main/pg_hba.conf
# Verificar línea: local all postgres md5
```

### Error: "peer authentication failed"
```bash
# Editar configuración de autenticación
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Cambiar línea:
# local   all             postgres                                peer
# A:
# local   all             postgres                                md5

# Reiniciar PostgreSQL
sudo service postgresql restart
```

### Error: "Permission denied"
```bash
# Dar permisos al usuario
sudo -u postgres psql
ALTER USER postgres CREATEDB;
\q

# O crear usuario específico
sudo -u postgres createuser --interactive tu_usuario
```

### Error: "No module named..."
```bash
# Verificar que venv está activo
echo $VIRTUAL_ENV

# Si no está activo
source venv/bin/activate

# Reinstalar dependencias si necesario
pip install -r requirements.txt
```

## 🎯 VENTAJAS WSL vs Windows Nativo

| Aspecto | WSL | Windows Nativo |
|---------|-----|----------------|
| PostgreSQL | ✅ Nativo Linux | ❌ Instalación compleja |
| Paths | ✅ Unix paths | ❌ Windows paths |
| Dependencias | ✅ apt install | ❌ Manual downloads |
| Compatibilidad | ✅ Como Docker | ❌ Diferencias |
| Performance | ✅ Mejor | ❌ Overhead |

## 📋 WORKFLOW DESARROLLO WSL

### Rutina Diaria
```bash
# 1. Entrar a WSL (desde Windows)
wsl

# 2. Ir al proyecto
cd ~/sistema-donaciones/mgen-backend

# 3. Activar ambiente
source venv/bin/activate

# 4. Iniciar PostgreSQL
sudo service postgresql start

# 5. Aplicar migraciones (si hay)
alembic upgrade head

# 6. Ejecutar servidor
uvicorn app.main:app --reload

# 7. Desarrollar... (usar VS Code con WSL extension)
```

### Comandos Útiles WSL
```bash
# Ver servicios corriendo
sudo service --status-all

# Reiniciar PostgreSQL
sudo service postgresql restart

# Ver logs PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*-main.log

# Conectar a BD desde WSL
psql -U postgres -h localhost -d donations_db

# Backup de BD
pg_dump -U postgres -h localhost donations_db > backup.sql
```

## 🔄 INTEGRACIÓN CON VS CODE

### Setup VS Code + WSL
```bash
# Instalar extensión WSL en VS Code
# Abrir proyecto desde WSL
code .

# VS Code detectará automáticamente:
# - Python interpreter del venv
# - Terminal WSL
# - Extensiones para WSL
```

## ✅ VALIDACIÓN COMPLETA

```bash
# Script de validación completa
#!/bin/bash

echo "🔍 Validando setup WSL..."

# 1. Python
python --version && echo "✅ Python OK" || echo "❌ Python FAIL"

# 2. Virtual env
echo $VIRTUAL_ENV && echo "✅ VirtualEnv OK" || echo "❌ VirtualEnv FAIL"

# 3. Dependencias
python -c "import structlog, sqlalchemy, alembic, psycopg2; print('✅ Dependencias OK')" || echo "❌ Dependencias FAIL"

# 4. PostgreSQL
sudo service postgresql status | grep "online" && echo "✅ PostgreSQL OK" || echo "❌ PostgreSQL FAIL"

# 5. Base de datos
psql -U postgres -h localhost -d donations_db -c "SELECT 1;" && echo "✅ BD Conexión OK" || echo "❌ BD FAIL"

# 6. Alembic
alembic current && echo "✅ Alembic OK" || echo "❌ Alembic FAIL"

# 7. FastAPI
python -c "from app.main import app; print('✅ FastAPI OK')" || echo "❌ FastAPI FAIL"

echo "🎉 Validación completada"
```

## 🆘 RESET COMPLETO (Si todo falla)

```bash
# 1. Parar servicios
sudo service postgresql stop

# 2. Limpiar ambiente Python
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Reset PostgreSQL
sudo -u postgres dropdb donations_db
sudo -u postgres createdb donations_db
sudo service postgresql start

# 4. Reset schema
psql -U postgres -h localhost -d donations_db -f schema.sql
alembic stamp head

# 5. Verificar
alembic current
python -c "from app.main import app; print('App OK')"
```

---

## 💡 RECOMENDACIÓN

**WSL es la mejor opción para desarrollo local** de este proyecto porque:
- ✅ Compatibilidad nativa con PostgreSQL
- ✅ Sin problemas de rutas/paths
- ✅ Mejor performance que Windows nativo
- ✅ Experiencia similar a Docker/Linux
- ✅ Fácil integración con VS Code

**El error `KeyError: '4a9d440c02ab'` se resuelve fácilmente en WSL siguiendo los pasos de diagnóstico y solución arriba.**



