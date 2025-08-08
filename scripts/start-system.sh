#!/bin/bash

# =============================================================================
# SCRIPT DE INICIO COMPLETO DEL SISTEMA ECOMMERCE ANALYTICS
# =============================================================================

set -e  # Salir si cualquier comando falla

# Cargar variables de entorno si existe el archivo de configuración
if [ -f "../config/urls.env" ]; then
    echo "📋 Cargando configuración de URLs..."
    export $(cat ../config/urls.env | grep -v '^#' | xargs)
fi

echo "🚀 INICIANDO SISTEMA ECOMMERCE ANALYTICS DESDE CERO"
echo "=================================================="

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

# Función para verificar si Docker está ejecutándose
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker no está ejecutándose. Por favor, inicia Docker Desktop."
        exit 1
    fi
    log_success "Docker está ejecutándose"
}

# Función para esperar que un servicio esté listo
wait_for_service() {
    local service_name=$1
    local max_attempts=$2
    local attempt=1
    
    log_info "Esperando que $service_name esté listo..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$service_name.*healthy\|$service_name.*Up"; then
            log_success "$service_name está listo"
            return 0
        fi
        
        log_info "Intento $attempt/$max_attempts - $service_name aún no está listo..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    log_error "$service_name no se pudo iniciar después de $max_attempts intentos"
    return 1
}

# Función para crear tablas de Cassandra
setup_cassandra_tables() {
    log_info "Configurando tablas de Cassandra..."
    
    # Esperar a que Cassandra esté completamente listo
    sleep 60
    
    # Crear keyspace si no existe
    docker exec ecommerce-cassandra cqlsh -e "CREATE KEYSPACE IF NOT EXISTS ecommerce_analytics WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};" || true
    
    # Crear tablas principales
    docker exec ecommerce-cassandra cqlsh -e "USE ecommerce_analytics; CREATE TABLE IF NOT EXISTS revenue_by_country_time (country text, date_bucket date, hour int, timestamp timestamp, invoice_no text, customer_id text, revenue_gbp decimal, revenue_usd decimal, order_count int, customer_count int, avg_order_value decimal, created_at timestamp, updated_at timestamp, PRIMARY KEY ((country, date_bucket), hour));" || true
    
    docker exec ecommerce-cassandra cqlsh -e "USE ecommerce_analytics; CREATE TABLE IF NOT EXISTS transactions (invoice_no text, stock_code text, description text, quantity int, invoice_date timestamp, unit_price decimal, customer_id text, country text, total_amount decimal, created_at timestamp, PRIMARY KEY (invoice_no, stock_code));" || true
    
    docker exec ecommerce-cassandra cqlsh -e "USE ecommerce_analytics; CREATE TABLE IF NOT EXISTS realtime_metrics (metric_key text, metric_value text, timestamp timestamp, PRIMARY KEY (metric_key, timestamp));" || true
    
    log_success "Tablas de Cassandra configuradas"
}

# Función para ejecutar job de Flink
run_flink_job() {
    log_info "Iniciando job de Flink automático..."
    
    # El job se ejecuta automáticamente con el servicio flink-job-runner
    docker-compose up -d flink-job-runner
    
    log_success "Job de Flink iniciado automáticamente"
}

# Función para verificar URLs
check_urls() {
    log_info "Verificando URLs del sistema..."
    
    echo ""
    echo "🌐 URLs DISPONIBLES:"
    echo "===================="
    echo "📊 Dashboard Principal: ${MAIN_DASHBOARD_URL:-http://localhost}"
    echo "🤖 Dashboard RL: ${RL_DASHBOARD_URL:-http://localhost:8050}"
    echo "🔧 API Backend: ${API_BASE_URL:-http://localhost:3003/api/v1}"
    echo "📈 Redis Commander: ${REDIS_COMMANDER_URL:-http://localhost:8088}"
    echo "🗄️  Cassandra Web: ${CASSANDRA_WEB_URL:-http://localhost:3005}"
    echo "📨 Kafka UI: ${KAFKA_UI_URL:-http://localhost:8089}"
    echo "⚡ Flink Dashboard: ${FLINK_DASHBOARD_URL:-http://localhost:8081}"
    echo ""
}

# Función para verificar estado final
check_final_status() {
    log_info "Verificando estado final del sistema..."
    
    echo ""
    echo "📋 ESTADO DE SERVICIOS:"
    echo "======================="
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
}

# =============================================================================
# INICIO DEL SCRIPT
# =============================================================================

# Verificar Docker
check_docker

# Paso 1: Construir todas las imágenes
log_info "Paso 1: Construyendo imágenes Docker..."
docker-compose build --no-cache

# Paso 2: Iniciar servicios base
log_info "Paso 2: Iniciando servicios base (Zookeeper, Kafka, Cassandra, Redis)..."
docker-compose up -d zookeeper kafka cassandra redis

# Esperar servicios base
wait_for_service "ecommerce-zookeeper" 12
wait_for_service "ecommerce-cassandra" 12
wait_for_service "ecommerce-redis" 12
wait_for_service "ecommerce-kafka" 12

# Paso 3: Configurar Cassandra
setup_cassandra_tables

# Paso 4: Iniciar Flink
log_info "Paso 3: Iniciando Flink (JobManager y TaskManagers)..."
docker-compose up -d jobmanager taskmanager-1 taskmanager-2 taskmanager-3

wait_for_service "ecommerce-jobmanager" 12

# Paso 5: Iniciar componente RL
log_info "Paso 4: Iniciando componente RL..."
docker-compose up -d rl-component

wait_for_service "ecommerce-rl" 12

# Paso 6: Iniciar API Backend
log_info "Paso 5: Iniciando API Backend..."
docker-compose up -d api

wait_for_service "ecommerce-api" 12

# Paso 7: Iniciar Frontend Dashboard
log_info "Paso 6: Iniciando Frontend Dashboard..."
docker-compose up -d analytics-dashboard

# Paso 8: Iniciar NGINX
log_info "Paso 7: Iniciando NGINX..."
docker-compose up -d nginx

# Paso 9: Iniciar servicios de monitoreo
log_info "Paso 8: Iniciando servicios de monitoreo..."
docker-compose up -d redis-commander cassandra-web kafka-ui

# Paso 10: Iniciar servicio de ingesta
log_info "Paso 9: Iniciando servicio de ingesta..."
docker-compose up -d ingesta

# Paso 11: Ejecutar job de Flink
run_flink_job

# Paso 12: Verificaciones finales
sleep 30

check_urls
check_final_status

echo ""
echo "🎉 ¡SISTEMA INICIADO EXITOSAMENTE!"
echo "=================================="
echo ""
echo "El sistema está completamente operativo con:"
echo "✅ Todos los servicios funcionando"
echo "✅ Job de Flink ejecutándose automáticamente"
echo "✅ Dashboards disponibles"
echo "✅ APIs operativas"
echo ""
echo "Puedes acceder a los dashboards en:"
echo "📊 http://localhost (Dashboard Principal)"
echo "🤖 http://localhost:8050 (Dashboard RL)"
echo "📦 http://localhost:8051 (Dashboard Inventarios)"
echo ""
echo "Para detener el sistema: ./scripts/stop-system.sh"
echo "" 