# 📊 E-commerce Analytics Dashboard

Dashboard completo para visualizar y analizar datos de e-commerce usando **Cassandra** y **Redis** como fuentes de datos.

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Databases     │
│   React + Vite  │────│   Node.js       │────│   Cassandra     │
│   Port: 5173    │    │   Port: 3001    │    │   Port: 9042    │
│                 │    │                 │    │                 │
│   Dashboard UI  │    │   REST API      │    │   Redis Cache   │
│   Charts/Tables │    │   Cache Layer   │    │   Port: 6379    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Inicialización Paso a Paso

### **Paso 1: Verificar que Cassandra y Redis estén funcionando**

```bash
# Verificar Cassandra
docker exec ecommerce-cassandra cqlsh -e "USE ecommerce_analytics; SELECT * FROM revenue_by_country_time LIMIT 5;"

# Verificar Redis
docker exec ecommerce-redis redis-cli ping
```

### **Paso 2: Configurar el Backend**

```bash
# Ir al directorio del backend
cd app/backend

# Instalar dependencias
npm install

# Crear archivo .env
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

# Iniciar el servidor backend
npm run dev
```

### **Paso 3: Configurar el Frontend**

```bash
# Abrir nueva terminal
cd app/frontend

# Instalar dependencias
npm install

# Crear archivo vite.config.js
cat > vite.config.js << EOF
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

# Crear archivos adicionales necesarios
mkdir -p src

# Crear main.jsx
cat > src/main.jsx << EOF
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

# Crear App.css
cat > src/App.css << EOF
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

# Crear index.html
cat > index.html << EOF
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>E-commerce Analytics Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOF

# Iniciar el servidor frontend
npm run dev
```

### **Paso 4: Verificar la instalación**

1. **Backend API**: http://localhost:3001/api/v1
2. **Frontend Dashboard**: http://localhost:5173
3. **Health Check**: http://localhost:3001/health

## 📊 Endpoints Disponibles

### **Revenue Analytics**
- `GET /api/v1/revenue/country/:country` - Revenue por país
- `GET /api/v1/revenue/summary` - Resumen global
- `GET /api/v1/revenue/realtime` - Datos en tiempo real
- `GET /api/v1/revenue/countries` - Lista de países
- `GET /api/v1/revenue/stats` - Estadísticas generales

### **Ejemplos de uso:**

```bash
# Obtener revenue del Reino Unido
curl "http://localhost:3001/api/v1/revenue/country/United%20Kingdom?startDate=2025-07-01&endDate=2025-07-04"

# Obtener resumen global
curl "http://localhost:3001/api/v1/revenue/summary"

# Obtener datos en tiempo real
curl "http://localhost:3001/api/v1/revenue/realtime"

# Listar países disponibles
curl "http://localhost:3001/api/v1/revenue/countries"
```

## 🔧 Configuración de Cache

### **Redis Databases:**
- **DB 0**: Cache de API (5 minutos TTL)
- **DB 1**: Sesiones de usuario (30 minutos TTL)
- **DB 2**: Métricas en tiempo real (1 minuto TTL)

### **Estrategia de Cache:**
```javascript
// Datos históricos: 5 minutos
revenue:country:UK:2025-07-01:2025-07-04

// Datos en tiempo real: 1 minuto
revenue:realtime:all

// Listas estáticas: 1 hora
revenue:countries:list
```

## 🐳 Despliegue con Docker

### **Opción 1: Usar los servicios existentes**
```bash
# Usar los servicios Cassandra y Redis ya corriendo
cd app
docker-compose -f docker-compose.app.yml up --build
```

### **Opción 2: Todo desde cero**
```bash
# Iniciar todo el stack
docker-compose up -d

# Luego la aplicación
cd app
docker-compose -f docker-compose.app.yml up --build
```

## 📈 Funcionalidades del Dashboard

### **Dashboard Principal**
- **Métricas globales**: Revenue total, órdenes, clientes, países
- **Tiempo real**: Actividad de las últimas 24 horas
- **Alertas**: Indicadores de estado del sistema

### **Análisis de Revenue**
- **Filtros**: Por país y rango de fechas
- **Gráficos**: Line chart (revenue) y bar chart (órdenes)
- **Tabla detallada**: Datos transaccionales completos

### **Métricas en Tiempo Real**
- **Monitoreo**: Países activos, revenue actual
- **Actualizaciones**: Auto-refresh cada minuto
- **Alertas**: Anomalías y tendencias

## 🔍 Monitoreo y Logs

### **Health Checks**
```bash
# API Health
curl http://localhost:3001/health

# Verificar conexiones
curl http://localhost:3001/api/v1 | jq .
```

### **Logs del Backend**
```bash
# Logs en tiempo real
cd app/backend
npm run dev

# O con Docker
docker logs -f ecommerce-analytics-api
```

### **Métricas de Redis**
```bash
# Info de Redis
docker exec ecommerce-redis redis-cli INFO

# Ver keys cacheadas
docker exec ecommerce-redis redis-cli KEYS "revenue:*"
```

## 🚨 Troubleshooting

### **Error: Cannot connect to Cassandra**
```bash
# Verificar que Cassandra esté running
docker ps | grep cassandra

# Restart si es necesario
docker restart ecommerce-cassandra

# Verificar logs
docker logs ecommerce-cassandra
```

### **Error: Redis connection failed**
```bash
# Verificar Redis
docker exec ecommerce-redis redis-cli ping

# Verificar configuración
docker exec ecommerce-redis redis-cli CONFIG GET databases
```

### **Error: CORS issues**
```bash
# Verificar ALLOWED_ORIGINS en .env
echo $ALLOWED_ORIGINS

# Reiniciar backend con nueva configuración
npm run dev
```

## 🔧 Desarrollo

### **Agregar nuevos endpoints**
1. Crear servicio en `src/services/`
2. Crear controlador en `src/controllers/`
3. Agregar rutas en `src/server.js`

### **Agregar nuevas visualizaciones**
1. Instalar dependencia: `npm install nueva-libreria`
2. Crear componente en `src/components/`
3. Importar en `App.jsx`

### **Optimizaciones de Performance**
- **Cassandra**: Usar prepared statements
- **Redis**: Configurar TTL apropiado
- **API**: Implementar paginación
- **Frontend**: Usar React.memo y useMemo

## 📚 Recursos Adicionales

- **Cassandra Web UI**: http://localhost:3000
- **Redis Commander**: http://localhost:8081 (admin/admin123)
- **API Documentation**: http://localhost:3001/api/v1
- **Health Monitor**: http://localhost:3001/health

---

¡Tu aplicación está lista para consumir y visualizar todos los datos de tu proyecto de e-commerce analytics! 🎉 