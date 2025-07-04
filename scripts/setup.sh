#!/bin/bash

echo "🚀 Setting up E-commerce Big Data project..."

# Create data directories
mkdir -p data/cassandra/{data,commitlog,saved_caches}

# Set permissions
chmod -R 777 data/

# Start Cassandra
echo "🐳 Starting Cassandra cluster..."
docker-compose up -d cassandra

# Wait for Cassandra to be ready
echo "⏰ Waiting for Cassandra to start..."
sleep 60

# Initialize schemas
echo "📊 Creating database schemas..."
docker exec -i ecommerce-cassandra cqlsh < cassandra/schemas/01-keyspace.cql
docker exec -i ecommerce-cassandra cqlsh < cassandra/schemas/02-tables.cql

# Start web UI
echo "🌐 Starting Cassandra Web UI..."
docker-compose up -d cassandra-web

echo "✅ Setup complete!"
echo "📊 Cassandra: http://localhost:9042"
echo "🌐 Web UI: http://localhost:3000"
echo "🔍 Connect with: docker exec -it ecommerce-cassandra cqlsh"