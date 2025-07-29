#!/bin/bash

echo "🚀 Iniciando generación de datos de inventario para RL..."

# Verificar si estamos en el directorio correcto
if [ ! -f "generate_inventory_data.py" ]; then
    echo "❌ Error: No se encuentra generate_inventory_data.py"
    echo "📁 Cambiando al directorio de scripts..."
    cd /opt/rl/scripts
fi

# Instalar dependencias Python
echo "📦 Instalando dependencias Python..."
pip install -r requirements.txt

# Ejecutar el script de generación
echo "🏭 Ejecutando generación de datos..."
python3 generate_inventory_data.py

# Verificar los datos generados
echo "🔍 Verificando datos generados..."
python3 verify_inventory_data.py

echo "✅ ¡Proceso completado!" 