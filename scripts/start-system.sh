#!/bin/bash

echo "🚀 Iniciando sistema de análisis de E-commerce..."

# Crear directorios necesarios
echo "📁 Creando directorios de datos..."
mkdir -p data/cassandra
mkdir -p data/redis
mkdir -p data/kafka
mkdir -p data/flink/checkpoints
mkdir -p data/flink/savepoints
mkdir -p data/zookeeper

# Iniciar servicios base
echo "🌟 Iniciando servicios base..."
docker-compose up -d zookeeper kafka cassandra redis

# Esperar que Kafka esté listo
echo "⏳ Esperando que Kafka esté disponible..."
while ! docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092 > /dev/null 2>&1; do
    sleep 5
done

# Crear topics de Kafka
echo "📨 Creación de tópicos delegada al contenedor kafka-topic-init..."

# Esperar que Cassandra esté lista
echo "⏳ Esperando que Cassandra esté disponible..."
while ! docker-compose exec cassandra nodetool status | grep "UN" > /dev/null 2>&1; do
    sleep 5
done

# Inicializar esquemas de Cassandra
echo "📊 Inicializando esquemas de Cassandra..."
docker-compose exec cassandra cqlsh -f /docker-entrypoint-initdb.d/01-keyspace.cql
docker-compose exec cassandra cqlsh -f /docker-entrypoint-initdb.d/02-tables.cql

# Iniciar servicios de procesamiento
echo "🔄 Iniciando servicios de procesamiento..."
docker-compose up -d jobmanager taskmanager-1 taskmanager-2 taskmanager-3

# Esperar que Flink esté listo
echo "⏳ Esperando que Flink esté disponible..."
while ! curl -s http://localhost:8081 > /dev/null; do
    sleep 5
done

# Iniciar job de Flink
echo "🔄 Iniciando job de procesamiento de Flink..."
docker-compose exec jobmanager flink run -d /opt/flink/jobs/transaction_processor.py

# Iniciar servicios de monitoreo
echo "🔍 Iniciando servicios de monitoreo..."
docker-compose up -d kafka-ui cassandra-web redis-commander

# Iniciar servicios de aplicación
echo "🌐 Iniciando servicios de aplicación..."
docker-compose -f 6.0_app/docker-compose.app.yml up -d ecommerce-api ecommerce-dashboard nginx

# Nota: ingesta de datos no se inicia automáticamente.  
# Para lanzar la ingesta manualmente usa:
#   docker-compose up -d ingesta
# o bien:
#   docker-compose run --rm ingesta
# según tu flujo.

echo "✅ Sistema iniciado completamente (sin ingesta)!"
echo ""
echo "🔗 Servicios disponibles:"
echo "📊 Flink Dashboard: http://localhost:8081"
echo "🎯 Kafka UI: http://localhost:8080"
echo "💾 Cassandra Web: http://localhost:3000"
echo "📝 Redis Commander: http://localhost:8082"
echo "🌐 Frontend: http://localhost"
echo "🔌 API: http://localhost/api/v1" 