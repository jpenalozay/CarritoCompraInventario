#!/bin/bash

echo "🔍 VALIDACIÓN DEL SISTEMA E-COMMERCE CON RL"
echo "============================================="

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
PASSED=0
FAILED=0

# Función para testear servicios
test_service() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "🔎 Verificando $name... "
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
    fi
}

# Función para testear contenedores
test_container() {
    local name=$1
    local container=$2
    
    echo -n "🐳 Verificando contenedor $name... "
    
    if docker ps | grep -q "$container.*Up"; then
        echo -e "${GREEN}✅ RUNNING${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ NOT RUNNING${NC}"
        ((FAILED++))
        echo "   Logs: docker logs $container"
    fi
}

# Función para testear datos en Cassandra
test_cassandra_data() {
    local table=$1
    local description=$2
    
    echo -n "📊 Verificando datos en $table... "
    
    local count=$(docker-compose exec cassandra cqlsh -e "USE ecommerce_analytics; SELECT COUNT(*) FROM $table;" 2>/dev/null | grep -o '[0-9]\+' | tail -1)
    
    if [ -n "$count" ] && [ "$count" -gt 0 ]; then
        echo -e "${GREEN}✅ $count registros${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ Sin datos${NC}"
        ((FAILED++))
    fi
}

echo "🚀 Iniciando validación del sistema..."
echo ""

# CONTENEDORES
echo "📦 VERIFICANDO CONTENEDORES:"
test_container "Zookeeper" "ecommerce-zookeeper"
test_container "Kafka" "ecommerce-kafka"
test_container "Cassandra" "ecommerce-cassandra"
test_container "Redis" "ecommerce-redis"
test_container "Flink JobManager" "ecommerce-jobmanager"
test_container "TaskManager 1" "ecommerce-taskmanager-1"
test_container "RL Component" "ecommerce-rl"
test_container "API Backend" "ecommerce-api"
test_container "Dashboard" "ecommerce-dashboard"
echo ""

# SERVICIOS HTTP
echo "🌐 VERIFICANDO SERVICIOS HTTP:"
test_service "Flink Dashboard" "http://localhost:8081"
test_service "RL API Health" "http://localhost:5000/health"
test_service "RL Dashboard" "http://localhost:8050"
test_service "API Backend" "http://localhost:3003/health"
test_service "Frontend Dashboard" "http://localhost:5174"
test_service "Kafka UI" "http://localhost:8089"
test_service "Cassandra Web" "http://localhost:3005"
test_service "Redis Commander" "http://localhost:8088"
echo ""

# DATOS EN CASSANDRA
echo "💾 VERIFICANDO DATOS EN CASSANDRA:"
test_cassandra_data "inventory_current" "Inventario actual"
test_cassandra_data "product_costs" "Costos de productos"
test_cassandra_data "suppliers" "Proveedores"
test_cassandra_data "demand_metrics" "Métricas de demanda"
test_cassandra_data "warehouse_config" "Configuración almacén"
test_cassandra_data "rl_model_metrics" "Métricas RL"
echo ""

# FUNCIONALIDAD RL
echo "🤖 VERIFICANDO FUNCIONALIDAD RL:"
echo -n "🔎 Verificando endpoint de métricas RL... "
rl_metrics=$(curl -s "http://localhost:5000/api/v1/rl/agent/state" 2>/dev/null)
if echo "$rl_metrics" | grep -q "q_table_size"; then
    echo -e "${GREEN}✅ API RL funcionando${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ API RL no responde correctamente${NC}"
    ((FAILED++))
fi

echo -n "🔎 Verificando datos de inventario para RL... "
inv_data=$(curl -s "http://localhost:5001/api/inventory/status" 2>/dev/null)
if echo "$inv_data" | grep -q "stock_code"; then
    echo -e "${GREEN}✅ API de Inventario funcionando${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  API de Inventario no responde (esperado si no está habilitado)${NC}"
fi
echo ""

# KAFKA TOPICS
echo "📨 VERIFICANDO KAFKA:"
echo -n "🔎 Verificando tópicos de Kafka... "
topics=$(docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null)
if echo "$topics" | grep -q "ecommerce_transactions"; then
    echo -e "${GREEN}✅ Tópicos creados${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Tópicos no encontrados${NC}"
    ((FAILED++))
fi
echo ""

# REDIS
echo "📝 VERIFICANDO REDIS:"
echo -n "🔎 Verificando conexión Redis... "
if docker-compose exec redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✅ Redis funcionando${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Redis no responde${NC}"
    ((FAILED++))
fi
echo ""

# RESUMEN
echo "📊 RESUMEN DE VALIDACIÓN:"
echo "========================="
echo -e "✅ Pruebas pasadas: ${GREEN}$PASSED${NC}"
echo -e "❌ Pruebas fallidas: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!${NC}"
    echo ""
    echo "🚀 URLS PRINCIPALES:"
    echo "• RL Dashboard: http://localhost:8050"
    echo "• API RL: http://localhost:5000/health"
    echo "• Dashboard Principal: http://localhost:5174"
    echo "• API Backend: http://localhost:3003"
    echo ""
    echo "🎯 El dashboard de RL debería mostrar datos reales ahora."
    exit 0
else
    echo -e "${RED}⚠️  SISTEMA TIENE PROBLEMAS${NC}"
    echo ""
    echo "🔧 COMANDOS DE DEPURACIÓN:"
    echo "docker-compose logs rl-component"
    echo "docker-compose logs api"
    echo "docker-compose logs cassandra"
    echo "docker ps -a"
    echo ""
    echo "🔄 Para reiniciar:"
    echo "./scripts/initialize_complete_system.sh"
    exit 1
fi 