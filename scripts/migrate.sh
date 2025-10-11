#!/bin/bash

# Script de migración para Alembic
# Uso: ./scripts/migrate.sh [upgrade|downgrade|revision|current|history]

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
    error "Este script debe ejecutarse desde el directorio raíz del proyecto"
    exit 1
fi

# Verificar que Docker esté funcionando
if ! docker-compose ps | grep -q "donations-db"; then
    error "La base de datos no está ejecutándose. Ejecuta 'docker-compose up -d' primero."
    exit 1
fi

ACTION=${1:-upgrade}

case $ACTION in
    "upgrade")
        log "Ejecutando migración hacia adelante..."
        docker-compose exec api alembic upgrade head
        log "Migración completada exitosamente"
        ;;
    "downgrade")
        REVISION=${2:-"-1"}
        log "Ejecutando downgrade a revisión: $REVISION"
        docker-compose exec api alembic downgrade $REVISION
        log "Downgrade completado exitosamente"
        ;;
    "revision")
        MESSAGE=${2:-"New migration"}
        log "Creando nueva revisión: $MESSAGE"
        docker-compose exec api alembic revision --autogenerate -m "$MESSAGE"
        log "Revisión creada exitosamente"
        ;;
    "current")
        log "Estado actual de las migraciones:"
        docker-compose exec api alembic current
        ;;
    "history")
        log "Historial de migraciones:"
        docker-compose exec api alembic history
        ;;
    "stamp")
        REVISION=${2:-"head"}
        log "Marcando base de datos en revisión: $REVISION"
        docker-compose exec api alembic stamp $REVISION
        log "Base de datos marcada exitosamente"
        ;;
    "help"|"-h"|"--help")
        echo "Script de migración para Alembic"
        echo ""
        echo "Uso: $0 [COMANDO] [OPCIONES]"
        echo ""
        echo "Comandos disponibles:"
        echo "  upgrade [revisión]  - Ejecuta migraciones hacia adelante (default: head)"
        echo "  downgrade [revisión] - Ejecuta downgrade a revisión específica (default: -1)"
        echo "  revision [mensaje]  - Crea nueva revisión con mensaje (default: 'New migration')"
        echo "  current             - Muestra estado actual de migraciones"
        echo "  history             - Muestra historial de migraciones"
        echo "  stamp [revisión]    - Marca base de datos en revisión específica"
        echo "  help                - Muestra esta ayuda"
        echo ""
        echo "Ejemplos:"
        echo "  $0 upgrade                    # Migra a la última versión"
        echo "  $0 revision 'Add new table'   # Crea revisión con mensaje"
        echo "  $0 downgrade -1               # Revierte una migración"
        ;;
    *)
        error "Comando desconocido: $ACTION"
        echo "Ejecuta '$0 help' para ver comandos disponibles"
        exit 1
        ;;
esac
