#!/bin/bash

# ========================================
# SCRIPT DE INICIO PARA DESARROLLO
# ========================================

echo "🚀 Iniciando E-commerce Analytics Dashboard..."
echo ""

# Verificar que Docker esté corriendo
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker no está corriendo. Por favor inicia Docker primero."
    exit 1
fi

# Verificar que los servicios principales estén corriendo
echo "🔍 Verificando servicios principales..."

if ! docker ps | grep -q "ecommerce-cassandra"; then
    echo "❌ Cassandra no está corriendo. Ejecuta primero:"
    echo "   cd .. && docker-compose up -d cassandra"
    exit 1
fi

if ! docker ps | grep -q "ecommerce-redis"; then
    echo "❌ Redis no está corriendo. Ejecuta primero:"
    echo "   cd .. && docker-compose up -d redis"
    exit 1
fi

echo "✅ Servicios principales están corriendo"
echo ""

# Función para verificar si un puerto está en uso
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Verificar conexiones
echo "🔗 Verificando conexiones a bases de datos..."

# Test Cassandra
if docker exec ecommerce-cassandra cqlsh -e "USE ecommerce_analytics; SELECT COUNT(*) FROM revenue_by_country_time;" > /dev/null 2>&1; then
    echo "✅ Cassandra: Conectado y con datos"
else
    echo "⚠️  Cassandra: Conectado pero verificar datos"
fi

# Test Redis
if docker exec ecommerce-redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis: Conectado"
else
    echo "❌ Redis: Error de conexión"
    exit 1
fi

echo ""

# Configurar backend
echo "📊 Configurando Backend API..."
cd backend

if [ ! -f "package.json" ]; then
    echo "❌ No se encontró package.json en backend/"
    echo "   Asegúrate de estar en el directorio correcto"
    exit 1
fi

# Instalar dependencias del backend si no existen
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependencias del backend..."
    npm install
fi

# Crear .env si no existe
if [ ! -f ".env" ]; then
    echo "⚙️  Creando archivo .env..."
    cat > .env << EOF
NODE_ENV=development
PORT=3001
API_VERSION=v1

# Cassandra Configuration
CASSANDRA_HOSTS=localhost
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=ecommerce_analytics
CASSANDRA_USERNAME=cassandra
CASSANDRA_PASSWORD=cassandra
CASSANDRA_DATACENTER=datacenter1

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=ecommerce123
REDIS_DB_API_CACHE=0
REDIS_DB_SESSIONS=1
REDIS_DB_METRICS=2

# Security & Performance
JWT_SECRET=ecommerce_analytics_jwt_secret_2025
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=1000
CACHE_TTL_SECONDS=300

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
    echo "✅ Archivo .env creado"
fi

# Iniciar backend en background
echo "🚀 Iniciando Backend API..."
if check_port 3001; then
    echo "⚠️  Puerto 3001 ya está en uso, omitiendo inicio del backend"
else
    npm run dev > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "✅ Backend iniciado (PID: $BACKEND_PID)"
fi

# Configurar frontend
echo ""
echo "🌐 Configurando Frontend Dashboard..."
cd ../frontend

if [ ! -f "package.json" ]; then
    echo "❌ No se encontró package.json en frontend/"
    exit 1
fi

# Instalar dependencias del frontend si no existen
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependencias del frontend..."
    npm install
fi

# Crear archivos necesarios del frontend
if [ ! -f "vite.config.js" ]; then
    echo "⚙️  Creando vite.config.js..."
    cat > vite.config.js << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true
  },
  define: {
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify('http://localhost:3001/api/v1')
  }
})
EOF
fi

if [ ! -f "index.html" ]; then
    echo "⚙️  Creando index.html..."
    cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>E-commerce Analytics Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOF
fi

if [ ! -f "src/main.jsx" ]; then
    mkdir -p src
    echo "⚙️  Creando src/main.jsx..."
    cat > src/main.jsx << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import 'antd/dist/reset.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
EOF
fi

if [ ! -f "src/App.css" ]; then
    echo "⚙️  Creando src/App.css..."
    cat > src/App.css << 'EOF'
.ant-layout {
  background: #f0f2f5;
}

.ant-layout-header {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
}

.ant-card {
  border-radius: 8px;
  box-shadow: 0 1px 2px 0 rgba(0,0,0,0.03), 0 1px 6px -1px rgba(0,0,0,0.02), 0 2px 4px 0 rgba(0,0,0,0.02);
}

.ant-statistic-content-value {
  font-size: 24px;
  font-weight: 600;
}

.recharts-wrapper {
  margin: 0 auto;
}
EOF
fi

# Crear directorio de logs
mkdir -p ../logs

# Esperar a que el backend esté listo
echo "⏳ Esperando a que el backend esté listo..."
sleep 5

# Verificar que el backend esté respondiendo
for i in {1..30}; do
    if curl -s http://localhost:3001/health > /dev/null 2>&1; then
        echo "✅ Backend está respondiendo"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend no está respondiendo después de 30 intentos"
        exit 1
    fi
    sleep 1
done

# Iniciar frontend
echo "🚀 Iniciando Frontend Dashboard..."
if check_port 5173; then
    echo "⚠️  Puerto 5173 ya está en uso, omitiendo inicio del frontend"
else
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "✅ Frontend iniciado (PID: $FRONTEND_PID)"
fi

# Esperar a que el frontend esté listo
echo "⏳ Esperando a que el frontend esté listo..."
sleep 10

echo ""
echo "🎉 ====================================="
echo "✅ APLICACIÓN INICIADA EXITOSAMENTE"
echo "🎉 ====================================="
echo ""
echo "🌐 URLs disponibles:"
echo "   📊 Dashboard:        http://localhost:5173"
echo "   🔧 API Backend:      http://localhost:3001/api/v1"
echo "   💚 Health Check:     http://localhost:3001/health"
echo ""
echo "🔗 Servicios externos:"
echo "   📊 Cassandra Web UI: http://localhost:3000"
echo "   🔄 Redis Commander:  http://localhost:8081 (admin/admin123)"
echo ""
echo "📋 Comandos útiles:"
echo "   Ver logs backend:    tail -f logs/backend.log"
echo "   Ver logs frontend:   tail -f logs/frontend.log"
echo "   Parar servicios:     ./scripts/stop-development.sh"
echo ""
echo "🎯 ¡Tu dashboard está listo para usar!"

# Guardar PIDs para poder parar los servicios después
echo "BACKEND_PID=$BACKEND_PID" > ../logs/pids.env
echo "FRONTEND_PID=$FRONTEND_PID" >> ../logs/pids.env

# Abrir el navegador automáticamente (opcional)
if command -v open >/dev/null 2>&1; then
    echo "🌐 Abriendo dashboard en el navegador..."
    sleep 3
    open http://localhost:5173
elif command -v xdg-open >/dev/null 2>&1; then
    echo "🌐 Abriendo dashboard en el navegador..."
    sleep 3
    xdg-open http://localhost:5173
fi 