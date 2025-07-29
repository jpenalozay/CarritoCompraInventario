#!/bin/bash

echo "⏳ Esperando que Docker Desktop se inicie..."
echo "💡 Por favor abre Docker Desktop manualmente desde el menú de inicio"
echo ""

# Contador
wait_time=0
max_wait=300  # 5 minutos máximo

while ! docker ps >/dev/null 2>&1; do
    if [ $wait_time -ge $max_wait ]; then
        echo "❌ Tiempo de espera agotado (5 minutos)"
        echo "🔧 Verifica que Docker Desktop esté instalado y funcionando"
        exit 1
    fi
    
    printf "."
    sleep 5
    wait_time=$((wait_time + 5))
    
    # Cada 30 segundos mostrar recordatorio
    if [ $((wait_time % 30)) -eq 0 ]; then
        echo ""
        echo "⏳ Esperando... ($wait_time segundos) - Abre Docker Desktop si no lo has hecho"
    fi
done

echo ""
echo "✅ ¡Docker Desktop está corriendo!"
echo "🚀 Ahora puedes ejecutar: ./scripts/start-system.sh" 