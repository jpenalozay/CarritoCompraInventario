#!/bin/bash

echo "🔍 Verificando montaje de esquemas de Cassandra..."

# Verificar que el contenedor esté corriendo
if ! docker ps | grep -q "ecommerce-cassandra"; then
    echo "❌ Contenedor de Cassandra no está corriendo"
    exit 1
fi

echo "✅ Contenedor de Cassandra está corriendo"

# Verificar archivos en el directorio de inicialización
echo "📁 Verificando archivos en /docker-entrypoint-initdb.d/..."
docker exec ecommerce-cassandra ls -la /docker-entrypoint-initdb.d/

echo ""
echo "🔍 Verificando contenido de archivos .cql..."

# Verificar que el keyspace se creó
echo "📊 Verificando keyspace ecommerce_analytics..."
docker exec ecommerce-cassandra cqlsh -e "DESCRIBE KEYSPACES;"

echo ""
echo "📋 Verificando tablas en ecommerce_analytics..."
docker exec ecommerce-cassandra cqlsh -e "USE ecommerce_analytics; DESCRIBE TABLES;"

echo ""
echo "✅ Verificación completada" 