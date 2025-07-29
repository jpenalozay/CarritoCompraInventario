FROM python:3.9-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ ./src/
COPY dashboard/ ./dashboard/

# Crear directorio para logs
RUN mkdir -p /app/logs

# Variables de entorno
ENV PYTHONPATH=/app
ENV RL_API_PORT=5000
ENV DASH_PORT=8050

# Exponer puertos
EXPOSE 5000 8050

# Script de inicio
COPY start_rl.sh .
RUN chmod +x start_rl.sh

# Comando por defecto
CMD ["./start_rl.sh"] 