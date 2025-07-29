#!/usr/bin/env python3
"""
Script completo para ejecutar todo el sistema RL de inventarios
"""
import sys
import os
import time
import logging
import json
import subprocess
from datetime import datetime

# Añadir directorio src al path
sys.path.append('/opt/rl/src')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_cassandra_connection():
    """Verificar conexión a Cassandra"""
    try:
        from cassandra.cluster import Cluster
        cluster = Cluster(['cassandra'])
        session = cluster.connect('ecommerce_analytics')
        
        # Test query
        result = session.execute("SELECT COUNT(*) FROM inventory_current")
        count = result.one()[0]
        
        logger.info(f"✅ Cassandra conectado - {count} productos en inventario")
        cluster.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error conectando a Cassandra: {e}")
        return False

def run_rl_training():
    """Ejecutar entrenamiento del agente RL"""
    try:
        logger.info("🎯 Iniciando entrenamiento del agente RL...")
        
        from inventory_rl_runner import InventoryRLRunner
        
        runner = InventoryRLRunner()
        episode_rewards = runner.run_simulation(episodes=20, days_per_episode=15)
        
        # Calcular estadísticas
        avg_reward = sum(episode_rewards) / len(episode_rewards)
        max_reward = max(episode_rewards)
        min_reward = min(episode_rewards)
        
        logger.info(f"📊 Entrenamiento completado:")
        logger.info(f"   📈 Recompensa promedio: {avg_reward:.2f}")
        logger.info(f"   📈 Recompensa máxima: {max_reward:.2f}")
        logger.info(f"   📈 Recompensa mínima: {min_reward:.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en entrenamiento RL: {e}")
        return False

def generate_recommendations():
    """Generar y guardar recomendaciones"""
    try:
        logger.info("💡 Generando recomendaciones...")
        
        from inventory_rl_runner import InventoryRLRunner
        
        runner = InventoryRLRunner()
        recommendations = runner.generate_recommendations()
        runner.save_recommendations_to_db(recommendations)
        
        # Mostrar resumen
        high_priority = [r for r in recommendations if r['priority'] == 'HIGH']
        medium_priority = [r for r in recommendations if r['priority'] == 'MEDIUM']
        
        logger.info(f"📋 Recomendaciones generadas:")
        logger.info(f"   🚨 Alta prioridad: {len(high_priority)}")
        logger.info(f"   ⚠️  Media prioridad: {len(medium_priority)}")
        logger.info(f"   ✅ Total: {len(recommendations)}")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"❌ Error generando recomendaciones: {e}")
        return []

def start_api_server():
    """Iniciar servidor API"""
    try:
        logger.info("🌐 Iniciando servidor API...")
        
        # Ejecutar API en background
        api_process = subprocess.Popen([
            'python3', '/opt/rl/src/inventory_api_extended.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Esperar un poco para que inicie
        time.sleep(3)
        
        # Verificar que esté corriendo
        if api_process.poll() is None:
            logger.info("✅ Servidor API iniciado en puerto 5002")
            return api_process
        else:
            logger.error("❌ Error iniciando servidor API")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error iniciando API: {e}")
        return None

def test_api_endpoints():
    """Probar endpoints del API"""
    try:
        import requests
        
        base_url = "http://localhost:5002"
        
        # Test health check
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Health check OK")
        else:
            logger.warning(f"⚠️ Health check failed: {response.status_code}")
        
        # Test inventory status
        response = requests.get(f"{base_url}/api/inventory/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Inventory status OK - {len(data['data'])} productos")
        else:
            logger.warning(f"⚠️ Inventory status failed: {response.status_code}")
        
        # Test recommendations
        response = requests.get(f"{base_url}/api/inventory/recommendations", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Recommendations OK - {len(data['data'])} recomendaciones")
        else:
            logger.warning(f"⚠️ Recommendations failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error probando API: {e}")
        return False

def create_dashboard_summary():
    """Crear resumen para dashboard"""
    try:
        from cassandra.cluster import Cluster
        
        cluster = Cluster(['cassandra'])
        session = cluster.connect('ecommerce_analytics')
        
        # Obtener estadísticas
        stats = {}
        
        # Total productos
        result = session.execute("SELECT COUNT(*) FROM inventory_current")
        stats['total_products'] = result.one()[0]
        
        # Total proveedores
        result = session.execute("SELECT COUNT(*) FROM suppliers WHERE active = true ALLOW FILTERING")
        stats['active_suppliers'] = result.one()[0]
        
        # Recomendaciones de hoy
        result = session.execute(
            "SELECT COUNT(*) FROM inventory_recommendations WHERE recommendation_date = ? ALLOW FILTERING",
            [datetime.now().date()]
        )
        stats['todays_recommendations'] = result.one()[0]
        
        # Eventos recientes
        result = session.execute(
            "SELECT COUNT(*) FROM inventory_events WHERE event_timestamp >= ? ALLOW FILTERING",
            [datetime.now().replace(hour=0, minute=0, second=0)]
        )
        stats['todays_events'] = result.one()[0]
        
        logger.info("📊 RESUMEN DEL SISTEMA RL:")
        logger.info(f"   📦 Productos en inventario: {stats['total_products']}")
        logger.info(f"   👥 Proveedores activos: {stats['active_suppliers']}")
        logger.info(f"   💡 Recomendaciones hoy: {stats['todays_recommendations']}")
        logger.info(f"   📝 Eventos hoy: {stats['todays_events']}")
        
        cluster.shutdown()
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error creando resumen: {e}")
        return {}

def main():
    """Función principal"""
    logger.info("🚀 INICIANDO SISTEMA COMPLETO DE RL PARA INVENTARIOS")
    logger.info("="*60)
    
    success_count = 0
    total_steps = 6
    
    # 1. Verificar conexión a Cassandra
    logger.info("1️⃣ Verificando conexión a Cassandra...")
    if test_cassandra_connection():
        success_count += 1
    else:
        logger.error("💥 Sistema abortado - no hay conexión a Cassandra")
        return False
    
    # 2. Ejecutar entrenamiento RL
    logger.info("\n2️⃣ Ejecutando entrenamiento del agente RL...")
    if run_rl_training():
        success_count += 1
    
    # 3. Generar recomendaciones
    logger.info("\n3️⃣ Generando recomendaciones...")
    recommendations = generate_recommendations()
    if recommendations:
        success_count += 1
    
    # 4. Iniciar servidor API
    logger.info("\n4️⃣ Iniciando servidor API...")
    api_process = start_api_server()
    if api_process:
        success_count += 1
    
    # 5. Probar endpoints
    logger.info("\n5️⃣ Probando endpoints del API...")
    if test_api_endpoints():
        success_count += 1
    
    # 6. Crear resumen
    logger.info("\n6️⃣ Creando resumen del sistema...")
    stats = create_dashboard_summary()
    if stats:
        success_count += 1
    
    # Resumen final
    logger.info("\n" + "="*60)
    logger.info(f"✅ SISTEMA COMPLETADO: {success_count}/{total_steps} pasos exitosos")
    
    if success_count == total_steps:
        logger.info("🎉 ¡SISTEMA RL DE INVENTARIOS TOTALMENTE FUNCIONAL!")
        logger.info("🌐 API disponible en: http://localhost:5002")
        logger.info("📊 Endpoints disponibles:")
        logger.info("   - GET /health")
        logger.info("   - GET /api/inventory/status")
        logger.info("   - GET /api/inventory/recommendations")
        logger.info("   - GET /api/inventory/suppliers")
        logger.info("   - GET /api/inventory/events")
        logger.info("   - GET /api/inventory/analytics/dashboard")
        
        # Mantener servidor corriendo
        if api_process:
            logger.info("\n🔄 Manteniendo servidor API activo...")
            logger.info("💡 Presiona Ctrl+C para detener")
            try:
                api_process.wait()
            except KeyboardInterrupt:
                logger.info("\n🛑 Deteniendo servidor...")
                api_process.terminate()
                api_process.wait()
                logger.info("✅ Servidor detenido")
    else:
        logger.warning(f"⚠️ Sistema parcialmente funcional ({success_count}/{total_steps})")
        if api_process:
            api_process.terminate()
    
    return success_count == total_steps

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n🛑 Sistema interrumpido por el usuario")
    except Exception as e:
        logger.error(f"💥 Error crítico: {e}")
        sys.exit(1) 