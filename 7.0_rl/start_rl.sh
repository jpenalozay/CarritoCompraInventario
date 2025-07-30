#!/bin/bash

echo "🚀 Iniciando componente de Reinforcement Learning para INVENTARIOS..."

# Esperar a que los servicios estén disponibles usando Python
echo "⏳ Verificando conectividad con servicios..."
python /app/src/check_cassandra.py
if [ $? -ne 0 ]; then
    echo "❌ Error verificando servicios"
    exit 1
fi

# Crear tablas RL si no existen
echo "📊 Verificando tablas de RL..."
python /app/src/init_rl_tables.py

# Generar datos de inventario si no existen
echo "📦 Generando datos de inventario..."
INVENTORY_API_PORT=5001 python /app/src/inventory_api.py --generate-data &
sleep 5

# Iniciar API RL de INVENTARIOS en background
echo "🌐 Iniciando API de RL de INVENTARIOS..."
cd /app/src
python rl_api.py &
RL_API_PID=$!

# Esperar a que la API esté lista
echo "⏳ Esperando que la API de RL esté lista..."
until curl -f http://localhost:5000/health > /dev/null 2>&1; do
    echo "API RL no está lista - esperando..."
    sleep 5
done
echo "✅ API de RL de INVENTARIOS está lista"

# Iniciar dashboard en background
echo "📊 Iniciando dashboard de RL..."
cd /app/dashboard
python rl_dashboard.py &
DASH_PID=$!

echo "✅ Componente RL de INVENTARIOS iniciado completamente"
echo "📦 API RL Inventarios: http://localhost:5000"
echo "📈 Dashboard RL: http://localhost:8050"

# Mantener el contenedor corriendo
wait $RL_API_PID $DASH_PID 