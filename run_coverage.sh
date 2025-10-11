#!/bin/bash
# Script para ejecutar tests con coverage

echo "🧪 Ejecutando tests con coverage..."
echo ""

# Verificar si estamos en Docker o local
if [ -f /.dockerenv ]; then
    # Estamos en Docker
    echo "📦 Detectado entorno Docker"
    pytest
else
    # Estamos en local, usar Docker
    echo "🐳 Ejecutando en contenedor Docker..."
    docker-compose exec -T api pytest
fi

echo ""
echo "✅ Tests completados!"
echo ""
echo "📊 Reportes generados:"
echo "  - Terminal: Ver arriba"
echo "  - HTML: htmlcov/index.html"
echo "  - JSON: coverage.json"
echo ""
echo "Para ver el reporte HTML:"
echo "  open htmlcov/index.html"
