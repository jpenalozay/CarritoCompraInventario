# 🚀 GUÍA DE INICIALIZACIÓN COMPLETA DEL SISTEMA E-COMMERCE CON RL

## ⚡ **INICIO RÁPIDO (2 pasos)**

### 1️⃣ **Inicia Docker Desktop**
- Abre **Docker Desktop** desde el menú de inicio
- Espera a que aparezca el ícono **verde** en la bandeja del sistema
- Confirma que Docker funciona: `docker --version`

### 2️⃣ **Ejecuta el script de inicialización**
```bash
./scripts/start-system.sh
```

**¡Eso es todo!** El script hace todo automáticamente.

---

## 🎯 **URLs PRINCIPALES DESPUÉS DE LA INICIALIZACIÓN**

### 📊 **Dashboards Principales**
- **🤖 RL Dashboard**: http://localhost:8050
- **🌐 Frontend Principal**: http://localhost:5174  
- **🔌 API Backend**: http://localhost:3003

### 🛠️ **Herramientas de Monitoreo**
- **📈 Flink Dashboard**: http://localhost:8081
- **📝 Kafka UI**: http://localhost:8089
- **💾 Cassandra Web**: http://localhost:3005
- **📮 Redis Commander**: http://localhost:8088

---

## ⏱️ **¿Cuánto tiempo toma?**

- **Inicialización completa**: 5-10 minutos
- **Dependiente de tu máquina**: La primera vez puede tomar más tiempo descargando imágenes Docker

---

## ✅ **¿Cómo verificar que todo funciona?**

### **Verificación rápida:**
```bash
# Verificar estado de contenedores
docker ps

# Verificar RL API
curl http://localhost:5000/health

# Verificar Backend API  
curl http://localhost:3003/health
```

### **Script de validación automática:**
```bash
./scripts/validate_system.sh
```

---

## 🔧 **¿Qué hace el script automáticamente?**

1. ✅ **Verifica Docker**
2. ✅ **Limpia estado anterior**
3. ✅ **Inicia servicios base** (Zookeeper, Kafka, Cassandra, Redis)
4. ✅ **Crea esquemas de base de datos**
5. ✅ **Genera datos de inventario para RL**
6. ✅ **Inicia Flink y procesamiento**
7. ✅ **Inicia sistema de Reinforcement Learning**
8. ✅ **Ejecuta ingesta de datos**
9. ✅ **Inicia APIs y dashboards**
10. ✅ **Inicia herramientas de monitoreo**

---

## 🎯 **PROBLEMA SOLUCIONADO: Dashboard mostrando ceros**

El script corregido incluye:
- ✅ **Datos reales de inventario** para el sistema RL
- ✅ **Métricas iniciales** del agente RL
- ✅ **Keyspaces consistentes** (ecommerce_analytics)
- ✅ **Inicialización completa** en orden correcto
- ✅ **Datos de transacciones** procesándose en tiempo real

---

## 🆘 **Resolución de Problemas**

### **Si el dashboard sigue mostrando ceros:**
```bash
# 1. Verificar estado del sistema
./scripts/validate_system.sh

# 2. Ver logs del sistema RL
docker logs ecommerce-rl

# 3. Reinicializar todo
docker-compose down -v
./scripts/start-system.sh
```

### **Si hay errores de puerto:**
```bash
# Ver qué procesos usan los puertos
netstat -an | findstr :8050
netstat -an | findstr :5000

# Detener todos los contenedores
docker-compose down
```

### **Si Docker no está corriendo:**
```bash
# Verificar Docker
docker --version
docker ps

# Si falla, reinicia Docker Desktop
```

---

## 📚 **Ayuda Adicional**

### **Ver todos los comandos disponibles:**
```bash
./scripts/help.sh
```

### **Logs útiles para depuración:**
```bash
docker logs ecommerce-rl          # Sistema RL
docker logs ecommerce-cassandra   # Base de datos
docker logs ecommerce-api         # API Backend
docker logs ecommerce-ingesta     # Ingesta de datos
```

---

## 🏗️ **Arquitectura del Sistema**

```
📊 Frontend (React) → 🔌 API (Node.js) → 💾 Cassandra
                                      ↗ 📮 Redis
🤖 RL Dashboard → 🧠 RL API → 💾 Cassandra
                           ↗ 📮 Redis

📨 Kafka ← 📥 Ingesta ← 📄 Excel Data
   ↓
🔄 Flink Jobs → 💾 Cassandra + 📮 Redis
```

---

## 🎉 **¡Éxito!**

**Si todo funciona correctamente, deberías ver:**

1. **RL Dashboard** con métricas reales (Q-table size: 125, epsilon: 0.1, etc.)
2. **Frontend Dashboard** con datos transaccionales
3. **Todos los servicios** corriendo en Docker
4. **APIs respondiendo** correctamente

**El dashboard de RL ya NO debería mostrar ceros!** 🎯 