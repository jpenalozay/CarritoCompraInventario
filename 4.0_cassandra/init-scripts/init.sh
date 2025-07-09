#!/bin/bash

# Esperar a que Cassandra esté lista
until cqlsh -e "describe keyspaces;" > /dev/null 2>&1; do
  echo "Esperando a que Cassandra esté lista..."
  sleep 5
done

echo "Cassandra está lista. Ejecutando scripts de inicialización..."

# Ejecutar scripts CQL
for f in /docker-entrypoint-initdb.d/*.cql; do
  case "$f" in
    *.cql)    echo "$0: running $f" && cqlsh -f "$f" ;;
  esac
  echo
done 