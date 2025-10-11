#!/bin/bash

# Script de migración para desarrollo local (WSL)
# Equivalente a los comandos de Docker pero para ambiente local

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "alembic.ini" ]; then
    error "Este script debe ejecutarse desde el directorio raíz del proyecto (mgen-backend)"
    exit 1
fi

# Verificar que el virtual environment está activo
if [ -z "$VIRTUAL_ENV" ]; then
    error "Virtual environment no está activo. Ejecuta 'source venv/bin/activate' primero."
    exit 1
fi

# Verificar que PostgreSQL está corriendo
if ! sudo service postgresql status | grep -q "online"; then
    error "PostgreSQL no está ejecutándose. Ejecuta 'sudo service postgresql start' primero."
    exit 1
fi

# Verificar conexión a la base de datos
if ! psql -U postgres -h localhost -d donations_db -c "SELECT 1;" &>/dev/null; then
    error "No se puede conectar a la base de datos donations_db"
    error "Verifica que PostgreSQL esté corriendo y que la BD exista"
    echo ""
    echo "Para crear la BD:"
    echo "  sudo -u postgres createdb donations_db"
    exit 1
fi

ACTION=${1:-upgrade}

case $ACTION in
    "upgrade")
        log "Ejecutando migración hacia adelante..."
        alembic upgrade head
        log "Migración completada exitosamente"
        ;;
    "downgrade")
        REVISION=${2:-"-1"}
        log "Ejecutando downgrade a revisión: $REVISION"
        alembic downgrade $REVISION
        log "Downgrade completado exitosamente"
        ;;
    "revision")
        MESSAGE=${2:-"New migration"}
        log "Creando nueva revisión: $MESSAGE"
        alembic revision --autogenerate -m "$MESSAGE"
        log "Revisión creada exitosamente"
        ;;
    "current")
        log "Estado actual de las migraciones:"
        alembic current
        ;;
    "history")
        log "Historial de migraciones:"
        alembic history
        ;;
    "stamp")
        REVISION=${2:-"head"}
        log "Marcando base de datos en revisión: $REVISION"
        alembic stamp $REVISION
        log "Base de datos marcada exitosamente"
        ;;
    "status")
        log "Estado completo del sistema:"
        echo ""
        echo "=== Virtual Environment ==="
        echo "VIRTUAL_ENV: $VIRTUAL_ENV"
        echo "Python: $(which python)"
        echo ""
        echo "=== PostgreSQL ==="
        sudo service postgresql status
        echo ""
        echo "=== Base de Datos ==="
        psql -U postgres -h localhost -d donations_db -c "\dt"
        echo ""
        echo "=== Alembic ==="
        alembic current
        ;;
    "setup")
        log "Configurando ambiente de desarrollo local..."
        
        # Verificar dependencias
        log "Verificando dependencias..."
        python -c "import structlog, sqlalchemy, alembic, psycopg2; print('✅ Todas las dependencias OK')" || {
            error "Faltan dependencias. Ejecuta 'pip install -r requirements.txt'"
            exit 1
        }
        
        # Verificar .env
        if [ ! -f ".env" ]; then
            warning "Archivo .env no encontrado. Creando desde env.example..."
            cp env.example .env
            warning "⚠️  Edita el archivo .env con tus configuraciones locales"
        fi
        
        # Verificar estado de BD
        log "Verificando estado de base de datos..."
        TABLE_COUNT=$(psql -U postgres -h localhost -d donations_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")
        
        if [ "$TABLE_COUNT" -eq "0" ]; then
            log "Base de datos vacía. Ejecutando migraciones..."
            alembic upgrade head
        else
            log "Base de datos tiene $TABLE_COUNT tablas. Verificando estado de Alembic..."
            if ! alembic current &>/dev/null; then
                warning "Alembic no está inicializado. Marcando como migrado..."
                alembic stamp head
            fi
        fi
        
        log "✅ Setup completado. Puedes ejecutar la aplicación con:"
        echo "    uvicorn app.main:app --reload"
        ;;
    "help"|"-h"|"--help")
        echo "Script de migración para desarrollo local (WSL)"
        echo ""
        echo "Uso: $0 [COMANDO] [OPCIONES]"
        echo ""
        echo "Comandos disponibles:"
        echo "  setup               - Configura el ambiente de desarrollo automáticamente"
        echo "  upgrade [revisión]  - Ejecuta migraciones hacia adelante (default: head)"
        echo "  downgrade [revisión] - Ejecuta downgrade a revisión específica (default: -1)"
        echo "  revision [mensaje]  - Crea nueva revisión con mensaje (default: 'New migration')"
        echo "  current             - Muestra estado actual de migraciones"
        echo "  history             - Muestra historial de migraciones"
        echo "  stamp [revisión]    - Marca base de datos en revisión específica"
        echo "  status              - Muestra estado completo del sistema"
        echo "  help                - Muestra esta ayuda"
        echo ""
        echo "Prerequisitos:"
        echo "  - Virtual environment activo: source venv/bin/activate"
        echo "  - PostgreSQL corriendo: sudo service postgresql start"
        echo "  - Base de datos creada: sudo -u postgres createdb donations_db"
        echo ""
        echo "Ejemplos:"
        echo "  $0 setup                      # Configura todo automáticamente"
        echo "  $0 upgrade                    # Migra a la última versión"
        echo "  $0 revision 'Add new table'   # Crea revisión con mensaje"
        echo "  $0 status                     # Ver estado completo"
        ;;
    *)
        error "Comando desconocido: $ACTION"
        echo "Ejecuta '$0 help' para ver comandos disponibles"
        exit 1
        ;;
esac





