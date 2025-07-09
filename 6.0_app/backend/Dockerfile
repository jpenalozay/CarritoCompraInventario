# ========================================
# DOCKERFILE PARA BACKEND API
# ========================================

# Usar imagen oficial de Node.js (LTS)
FROM node:18-alpine

# Información del mantenedor
LABEL maintainer="E-commerce Analytics Team"
LABEL version="1.0.0"
LABEL description="Backend API para E-commerce Analytics con Cassandra y Redis"

# Instalar curl para health check
RUN apk add --no-cache curl

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto de archivos
COPY . .

# Crear directorio de logs
RUN mkdir -p logs && \
    chown -R node:node logs

# Exponer puerto
EXPOSE 3001

# Comando de health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

# Comando para iniciar la aplicación
CMD ["npm", "start"] 