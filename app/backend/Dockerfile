# ========================================
# DOCKERFILE PARA BACKEND API
# ========================================

# Usar imagen oficial de Node.js (LTS)
FROM node:18-alpine

# Información del mantenedor
LABEL maintainer="E-commerce Analytics Team"
LABEL version="1.0.0"
LABEL description="Backend API para E-commerce Analytics con Cassandra y Redis"

# Instalar dependencias del sistema
RUN apk add --no-cache \
    curl \
    tzdata \
    && rm -rf /var/cache/apk/*

# Configurar zona horaria
ENV TZ=America/Mexico_City

# Crear usuario no-root para seguridad
RUN addgroup -g 1001 -S nodejs && \
    adduser -S backend -u 1001

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias de producción
RUN npm ci --only=production && \
    npm cache clean --force

# Copiar código fuente
COPY --chown=backend:nodejs . .

# Crear directorio de logs
RUN mkdir -p logs && \
    chown -R backend:nodejs logs

# Exponer puerto
EXPOSE 3001

# Cambiar a usuario no-root
USER backend

# Comando de health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

# Comando por defecto
CMD ["node", "src/server.js"] 