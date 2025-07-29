#!/bin/bash

echo "🚀 Starting Transaction Processor..."

# Ejecutar el procesador en el contenedor JobManager
docker exec -d ecommerce-jobmanager bash -c "cd /opt/flink/jobs && python3 kafka_to_cassandra.py"

echo "✅ Processor started in background"
echo "📊 To monitor progress:"
echo "   docker logs ecommerce-jobmanager --tail 20 -f"
echo ""
echo "🔍 To check data:"
echo "   docker exec ecommerce-cassandra bash -c \"cqlsh -e 'SELECT COUNT(*) FROM ecommerce_analytics.transactions;'\"" 