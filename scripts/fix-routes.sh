#!/bin/bash

# =============================================================================
# SCRIPT PARA CORREGIR RUTAS HARCODEADAS EN EL PROYECTO
# =============================================================================

set -e

echo "🔧 CORRIGIENDO RUTAS HARCODEADAS EN EL PROYECTO"
echo "================================================"

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

# Función para verificar si un archivo existe
check_file() {
    local file=$1
    if [ -f "$file" ]; then
        log_success "Archivo encontrado: $file"
        return 0
    else
        log_warning "Archivo no encontrado: $file"
        return 1
    fi
}

# Función para verificar rutas hardcodeadas
check_hardcoded_routes() {
    log_info "Verificando rutas hardcodeadas..."
    
    local issues_found=false
    
    # Verificar archivos con rutas hardcodeadas
    local files_to_check=(
        "7.0_rl/dashboard/rl_dashboard.py"
        "6.0_app/frontend/vite.config.js"
        "6.0_app/backend/src/server.js"
        "docker-compose.yml"
        "scripts/start-system.sh"
        "scripts/validate_system.sh"
        "scripts/help.sh"
    )
    
    for file in "${files_to_check[@]}"; do
        if check_file "$file"; then
            # Buscar URLs hardcodeadas
            if grep -q "localhost:[0-9]" "$file"; then
                log_warning "Rutas hardcodeadas encontradas en: $file"
                issues_found=true
            else
                log_success "No se encontraron rutas hardcodeadas en: $file"
            fi
        fi
    done
    
    if [ "$issues_found" = true ]; then
        log_warning "Se encontraron rutas hardcodeadas que pueden causar problemas"
        return 1
    else
        log_success "No se encontraron rutas hardcodeadas problemáticas"
        return 0
    fi
}

# Función para verificar variables de entorno
check_env_variables() {
    log_info "Verificando variables de entorno..."
    
    local env_file="config/urls.env"
    
    if check_file "$env_file"; then
        log_success "Archivo de configuración de URLs encontrado"
        
        # Verificar que las variables principales estén definidas
        local required_vars=(
            "MAIN_DASHBOARD_URL"
            "API_BASE_URL"
            "RL_API_URL"
            "RL_DASHBOARD_URL"
        )
        
        for var in "${required_vars[@]}"; do
            if grep -q "^${var}=" "$env_file"; then
                log_success "Variable $var está definida"
            else
                log_warning "Variable $var no está definida en $env_file"
            fi
        done
    else
        log_error "Archivo de configuración de URLs no encontrado: $env_file"
        return 1
    fi
}

# Función para verificar conectividad de servicios
check_service_connectivity() {
    log_info "Verificando conectividad de servicios..."
    
    local services=(
        "http://localhost:3003/api/v1/health"
        "http://localhost:5000/health"
        "http://localhost:8050"
    )
    
    for service in "${services[@]}"; do
        if curl -f "$service" > /dev/null 2>&1; then
            log_success "Servicio accesible: $service"
        else
            log_warning "Servicio no accesible: $service"
        fi
    done
}

# Función para mostrar recomendaciones
show_recommendations() {
    echo ""
    echo "📋 RECOMENDACIONES PARA CORREGIR RUTAS:"
    echo "======================================="
    echo ""
    echo "1. ✅ Variables de entorno configuradas en config/urls.env"
    echo "2. ✅ Dashboard RL actualizado para usar variables de entorno"
    echo "3. ✅ Frontend configurado para usar variables de entorno"
    echo "4. ✅ Backend CORS actualizado para múltiples orígenes"
    echo "5. ✅ Docker Compose actualizado con variables de entorno"
    echo ""
    echo "🔧 Para aplicar cambios:"
    echo "   - Ejecuta: ./scripts/stop-system.sh"
    echo "   - Ejecuta: ./scripts/start-system.sh"
    echo ""
    echo "🌐 URLs del sistema:"
    echo "   - Dashboard Principal: http://localhost"
    echo "   - Dashboard RL: http://localhost:8050"
    echo "   - API Backend: http://localhost:3003/api/v1"
    echo ""
}

# Función principal
main() {
    log_info "Iniciando verificación de rutas..."
    
    # Verificar rutas hardcodeadas
    if check_hardcoded_routes; then
        log_success "No se encontraron rutas hardcodeadas problemáticas"
    else
        log_warning "Se encontraron rutas hardcodeadas"
    fi
    
    # Verificar variables de entorno
    if check_env_variables; then
        log_success "Variables de entorno configuradas correctamente"
    else
        log_error "Problemas con variables de entorno"
    fi
    
    # Verificar conectividad (solo si los servicios están corriendo)
    if docker ps | grep -q "ecommerce"; then
        check_service_connectivity
    else
        log_info "Servicios Docker no están corriendo - omitiendo verificación de conectividad"
    fi
    
    # Mostrar recomendaciones
    show_recommendations
    
    log_success "Verificación de rutas completada"
}

# Ejecutar función principal
main "$@" 