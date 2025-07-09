#!/bin/bash

# Esperar a que Cassandra esté lista
echo "Esperando a que Cassandra esté lista..."
until cqlsh -e "describe keyspaces;" > /dev/null 2>&1; do
    echo "Cassandra no está lista - esperando..."
    sleep 5
done
echo "Cassandra está lista!"

# Ejecutar scripts CQL en orden
echo "Ejecutando scripts de inicialización..."

echo "Creando keyspace..."
cqlsh -f /docker-entrypoint-initdb.d/01-keyspace.cql

echo "Creando tablas..."
cqlsh -f /docker-entrypoint-initdb.d/02-tables.cql

echo "Insertando datos de ejemplo..."
cqlsh -f /docker-entrypoint-initdb.d/03-sample-data.cql

echo "Inicialización completada!"
