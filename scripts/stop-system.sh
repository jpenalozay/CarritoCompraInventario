#!/bin/bash

# =============================================================================
# SCRIPT DE PARADA COMPLETA DEL SISTEMA ECOMMERCE ANALYTICS
# =============================================================================

echo "🛑 DETENIENDO SISTEMA ECOMMERCE ANALYTICS"
echo "=========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detener todos los contenedores
log_info "Deteniendo todos los contenedores..."
docker-compose down

# Eliminar volúmenes (opcional - descomenta si quieres eliminar datos)
log_info "Eliminando volúmenes..."
docker volume prune -f

# Eliminar redes no utilizadas
log_info "Limpiando redes no utilizadas..."
docker network prune -f

# Eliminar imágenes no utilizadas (opcional)
log_info "Eliminando imágenes no utilizadas..."
docker image prune -a -f

log_success "Sistema detenido completamente"
echo ""
echo "✅ Todos los contenedores detenidos"
echo "✅ Volúmenes eliminados"
echo "✅ Redes limpiadas"
echo "✅ Imágenes no utilizadas eliminadas"
echo ""
echo "Para reiniciar el sistema: ./scripts/start-system.sh"
echo "" 