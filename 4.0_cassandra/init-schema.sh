#!/bin/bash

# Wait for Cassandra to be ready
until cqlsh -e "describe keyspaces" cassandra 9042; do
  echo "Cassandra is unavailable - sleeping"
  sleep 5
done

echo "Cassandra is up - executing schema"

# Execute schema files in order
echo "Creating keyspace..."
cqlsh -f /docker-entrypoint-initdb.d/01-keyspace.cql cassandra 9042

echo "Creating tables..."
cqlsh -f /docker-entrypoint-initdb.d/02-tables.cql cassandra 9042

echo "Inserting sample data..."
cqlsh -f /docker-entrypoint-initdb.d/03-sample-data.cql cassandra 9042

echo "Schema initialization completed" 