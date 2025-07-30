# 🔧 Corrección de Rutas Hardcodeadas - E-commerce Analytics

## Problema Identificado

El dashboard del sistema dejó de funcionar después de cambiar la ruta del proyecto debido a **rutas hardcodeadas** en varios archivos del proyecto. Esto es un problema común cuando las URLs están escritas directamente en el código en lugar de usar variables de entorno.

## Archivos Afectados

### 1. **Dashboard RL** (`7.0_rl/dashboard/rl_dashboard.py`)
**Problema:** URL hardcodeada del API RL
```python
# ANTES (línea 17)
RL_API_URL = "http://localhost:5000/api/v1/rl"

# DESPUÉS
RL_API_HOST = os.getenv('RL_API_HOST', 'localhost')
RL_API_PORT = os.getenv('RL_API_PORT', '5000')
RL_API_URL = f"http://{RL_API_HOST}:{RL_API_PORT}/api/v1/rl"
```

### 2. **Frontend** (`6.0_app/frontend/vite.config.js`)
**Problema:** URLs hardcodeadas en la configuración de Vite
```javascript
// ANTES
'import.meta.env.VITE_RL_API_URL': JSON.stringify('http://localhost:5000/api/v1'),
'import.meta.env.VITE_RL_DASHBOARD_URL': JSON.stringify('http://localhost:8050')

// DESPUÉS
'import.meta.env.VITE_RL_API_URL': JSON.stringify(process.env.VITE_RL_API_URL || 'http://localhost:5000/api/v1'),
'import.meta.env.VITE_RL_DASHBOARD_URL': JSON.stringify(process.env.VITE_RL_DASHBOARD_URL || 'http://localhost:8050')
```

### 3. **Backend** (`6.0_app/backend/src/server.js`)
**Problema:** CORS con orígenes hardcodeados
```javascript
// ANTES
origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000', 'http://localhost:5173'],

// DESPUÉS
origin: process.env.ALLOWED_ORIGINS?.split(',') || [
    'http://localhost:3000', 
    'http://localhost:5173', 
    'http://localhost:5174',
    'http://localhost:80',
    'http://localhost'
],
```

## Soluciones Implementadas

### 1. **Archivo de Configuración Centralizado** (`config/urls.env`)
Se creó un archivo centralizado para todas las URLs del sistema:
```bash
# URLs principales del sistema
MAIN_DASHBOARD_URL=http://localhost
API_BASE_URL=http://localhost:3003/api/v1
RL_API_URL=http://localhost:5000/api/v1
RL_DASHBOARD_URL=http://localhost:8050

# Variables de entorno para el frontend
VITE_API_BASE_URL=http://localhost:3003/api/v1
VITE_RL_API_URL=http://localhost:5000/api/v1
VITE_RL_DASHBOARD_URL=http://localhost:8050
```

### 2. **Variables de Entorno en Docker Compose**
Se agregaron variables de entorno al servicio RL:
```yaml
environment:
  - RL_API_HOST=localhost
  - RL_API_PORT=5000
  - DASH_PORT=8050
```

### 3. **Script de Verificación** (`scripts/fix-routes.sh`)
Se creó un script para verificar y corregir rutas automáticamente:
```bash
./scripts/fix-routes.sh
```

## Cómo Aplicar las Correcciones

### Opción 1: Reiniciar el Sistema Completo
```bash
# Detener el sistema
./scripts/stop-system.sh

# Iniciar el sistema con las nuevas configuraciones
./scripts/start-system.sh
```

### Opción 2: Verificar Rutas
```bash
# Ejecutar el script de verificación
./scripts/fix-routes.sh
```

### Opción 3: Reconstruir Contenedores Específicos
```bash
# Reconstruir solo el componente RL
docker-compose build rl-component
docker-compose up -d rl-component

# Reconstruir solo el frontend
docker-compose build analytics-dashboard
docker-compose up -d analytics-dashboard
```

## URLs del Sistema

Después de aplicar las correcciones, las URLs del sistema serán:

- **Dashboard Principal:** http://localhost
- **Dashboard RL:** http://localhost:8050
- **API Backend:** http://localhost:3003/api/v1
- **Redis Commander:** http://localhost:8088
- **Cassandra Web:** http://localhost:3005
- **Kafka UI:** http://localhost:8089
- **Flink Dashboard:** http://localhost:8081

## Verificación de Funcionamiento

### 1. Verificar Servicios
```bash
# Verificar que todos los contenedores estén corriendo
docker ps

# Verificar logs del componente RL
docker logs ecommerce-rl
```

### 2. Verificar APIs
```bash
# Verificar API RL
curl http://localhost:5000/health

# Verificar API Backend
curl http://localhost:3003/api/v1/health
```

### 3. Verificar Dashboards
```bash
# Verificar dashboard principal
curl http://localhost

# Verificar dashboard RL
curl http://localhost:8050
```

## Prevención de Problemas Futuros

### 1. **Usar Variables de Entorno**
Siempre usar variables de entorno en lugar de URLs hardcodeadas:
```python
# ✅ CORRECTO
API_URL = os.getenv('API_URL', 'http://localhost:3000')

# ❌ INCORRECTO
API_URL = "http://localhost:3000"
```

### 2. **Configuración Centralizada**
Mantener todas las URLs en archivos de configuración centralizados.

### 3. **Scripts de Verificación**
Usar scripts de verificación para detectar rutas hardcodeadas.

### 4. **Documentación**
Documentar todas las URLs y sus propósitos.

## Troubleshooting

### Problema: Dashboard RL no carga
**Solución:**
1. Verificar que el contenedor RL esté corriendo: `docker logs ecommerce-rl`
2. Verificar conectividad: `curl http://localhost:5000/health`
3. Reconstruir el contenedor: `docker-compose build rl-component`

### Problema: CORS errors en el frontend
**Solución:**
1. Verificar configuración CORS en el backend
2. Agregar el origen a `ALLOWED_ORIGINS`
3. Reiniciar el servicio backend

### Problema: APIs no responden
**Solución:**
1. Verificar variables de entorno en docker-compose.yml
2. Verificar conectividad entre contenedores
3. Revisar logs de los servicios

## Archivos Modificados

- ✅ `7.0_rl/dashboard/rl_dashboard.py`
- ✅ `6.0_app/frontend/vite.config.js`
- ✅ `6.0_app/backend/src/server.js`
- ✅ `docker-compose.yml`
- ✅ `scripts/start-system.sh`
- ✅ `config/urls.env` (nuevo)
- ✅ `scripts/fix-routes.sh` (nuevo)

## Estado Actual

✅ **Problemas identificados y corregidos**
✅ **Variables de entorno configuradas**
✅ **Scripts de verificación creados**
✅ **Documentación actualizada**

El sistema ahora debería funcionar correctamente independientemente de la ruta del proyecto. 