#!/bin/bash

# ========================================
# SCRIPT PARA PARAR DESARROLLO
# ========================================

echo "🛑 Parando E-commerce Analytics Dashboard..."
echo ""

# Ir al directorio correcto
cd "$(dirname "$0")/.."

# Verificar si existen PIDs guardados
if [ -f "logs/pids.env" ]; then
    source logs/pids.env
    
    if [ ! -z "$BACKEND_PID" ]; then
        echo "🔄 Parando Backend API (PID: $BACKEND_PID)..."
        if kill -TERM $BACKEND_PID 2>/dev/null; then
            echo "✅ Backend parado correctamente"
        else
            echo "⚠️  Backend PID no encontrado, intentando parar por puerto..."
            # Buscar proceso en puerto 3001
            BACKEND_PID_PORT=$(lsof -ti:3001)
            if [ ! -z "$BACKEND_PID_PORT" ]; then
                kill -TERM $BACKEND_PID_PORT
                echo "✅ Backend parado por puerto"
            fi
        fi
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "🌐 Parando Frontend Dashboard (PID: $FRONTEND_PID)..."
        if kill -TERM $FRONTEND_PID 2>/dev/null; then
            echo "✅ Frontend parado correctamente"
        else
            echo "⚠️  Frontend PID no encontrado, intentando parar por puerto..."
            # Buscar proceso en puerto 5173
            FRONTEND_PID_PORT=$(lsof -ti:5173)
            if [ ! -z "$FRONTEND_PID_PORT" ]; then
                kill -TERM $FRONTEND_PID_PORT
                echo "✅ Frontend parado por puerto"
            fi
        fi
    fi
    
    # Limpiar archivo de PIDs
    rm logs/pids.env
else
    echo "📝 No se encontró archivo de PIDs, buscando procesos por puerto..."
    
    # Parar proceso en puerto 3001 (Backend)
    BACKEND_PID=$(lsof -ti:3001)
    if [ ! -z "$BACKEND_PID" ]; then
        echo "🔄 Parando Backend en puerto 3001..."
        kill -TERM $BACKEND_PID
        echo "✅ Backend parado"
    else
        echo "ℹ️  No hay proceso corriendo en puerto 3001"
    fi
    
    # Parar proceso en puerto 5173 (Frontend)
    FRONTEND_PID=$(lsof -ti:5173)
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "🌐 Parando Frontend en puerto 5173..."
        kill -TERM $FRONTEND_PID
        echo "✅ Frontend parado"
    else
        echo "ℹ️  No hay proceso corriendo en puerto 5173"
    fi
fi

echo ""
echo "🧹 Limpiando archivos temporales..."

# Limpiar logs si existen
if [ -d "logs" ]; then
    rm -f logs/backend.log logs/frontend.log
    echo "✅ Logs limpiados"
fi

echo ""
echo "✅ ====================================="
echo "🛑 SERVICIOS PARADOS CORRECTAMENTE"
echo "✅ ====================================="
echo ""
echo "ℹ️  Los servicios de base de datos siguen corriendo:"
echo "   📊 Cassandra: docker ps | grep cassandra"
echo "   🔄 Redis:     docker ps | grep redis"
echo ""
echo "🔄 Para reiniciar la aplicación:"
echo "   ./scripts/start-development.sh"
echo ""
echo "🛑 Para parar todo el stack (incluyendo DB):"
echo "   cd .. && docker-compose down" 