#!/usr/bin/env bash

set -e

echo "🕒 Esperando que Kafka esté disponible..."
while ! kafka-topics --bootstrap-server kafka:9092 --list &>/dev/null; do
  sleep 5
done

echo "⚙️  Creando tópicos en Kafka..."
TOPICS=("ecommerce-united-kingdom" "ecommerce-germany" "ecommerce-france")
for topic in "${TOPICS[@]}"; do
  kafka-topics --create --if-not-exists \
    --bootstrap-server kafka:9092 \
    --replication-factor 1 \
    --partitions 3 \
    --topic "$topic" || true
  echo "  • $topic"
done

echo "✅ Tópicos creados (o ya existían)." 