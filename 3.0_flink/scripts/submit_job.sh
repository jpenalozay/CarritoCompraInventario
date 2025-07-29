#!/bin/bash

echo "Starting Flink Transaction Processor Job..."

# Cambiar al directorio de Flink
cd /opt/flink

# Ejecutar el job Python
python3 /opt/flink/jobs/transaction_processor.py &

echo "Job submitted in background. Check Flink dashboard for status." 