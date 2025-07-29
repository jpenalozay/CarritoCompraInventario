#!/usr/bin/env python3
"""
Script para verificar los datos de inventario generados en Cassandra
"""
import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_inventory_data():
    """Verificar que los datos de inventario se generaron correctamente"""
    cassandra_host = os.getenv('CASSANDRA_HOST', 'cassandra')
    cassandra_port = int(os.getenv('CASSANDRA_PORT', 9042))
    
    try:
        # Conectar a Cassandra
        cluster = Cluster([cassandra_host], port=cassandra_port)
        session = cluster.connect('ecommerce_analytics')
        
        logger.info("🔍 Verificando datos de inventario...")
        
        # Verificar inventory_current
        result = session.execute("SELECT COUNT(*) as count FROM inventory_current")
        inventory_count = result.one().count
        logger.info(f"📦 Productos en inventario: {inventory_count}")
        
        # Verificar suppliers
        result = session.execute("SELECT COUNT(*) as count FROM suppliers")
        supplier_count = result.one().count
        logger.info(f"👥 Proveedores: {supplier_count}")
        
        # Verificar product_costs
        result = session.execute("SELECT COUNT(*) as count FROM product_costs")
        cost_count = result.one().count
        logger.info(f"💰 Registros de costos: {cost_count}")
        
        # Verificar product_suppliers
        result = session.execute("SELECT COUNT(*) as count FROM product_suppliers")
        prod_supplier_count = result.one().count
        logger.info(f"🔗 Relaciones producto-proveedor: {prod_supplier_count}")
        
        # Verificar demand_metrics
        result = session.execute("SELECT COUNT(*) as count FROM demand_metrics")
        demand_count = result.one().count
        logger.info(f"📈 Métricas de demanda: {demand_count}")
        
        # Verificar inventory_events
        result = session.execute("SELECT COUNT(*) as count FROM inventory_events")
        event_count = result.one().count
        logger.info(f"📝 Eventos de inventario: {event_count}")
        
        # Verificar warehouse_config
        result = session.execute("SELECT COUNT(*) as count FROM warehouse_config")
        warehouse_count = result.one().count
        logger.info(f"🏢 Almacenes configurados: {warehouse_count}")
        
        # Mostrar algunos datos de ejemplo
        logger.info("\n📊 EJEMPLOS DE DATOS GENERADOS:")
        
        # Ejemplo de inventario
        result = session.execute("SELECT * FROM inventory_current LIMIT 3")
        logger.info("\n📦 Inventario Actual (3 ejemplos):")
        for row in result:
            logger.info(f"   • {row.stock_code}: Stock={row.current_stock}, Max={row.max_stock_capacity}, Reorder={row.reorder_point}")
        
        # Ejemplo de costos
        result = session.execute("SELECT * FROM product_costs LIMIT 3")
        logger.info("\n💰 Costos de Productos (3 ejemplos):")
        for row in result:
            logger.info(f"   • {row.stock_code}: Costo=${row.procurement_cost}, Clase={row.abc_classification}, Margen={row.profit_margin}")
        
        # Ejemplo de métricas de demanda
        result = session.execute("SELECT * FROM demand_metrics LIMIT 3")
        logger.info("\n📈 Métricas de Demanda (3 ejemplos):")
        for row in result:
            logger.info(f"   • {row.stock_code}: Demanda diaria={row.daily_demand_avg}, Tendencia={row.demand_trend}, Clase={row.velocity_category}")
        
        # Estadísticas por clasificación ABC
        result = session.execute("SELECT abc_classification, COUNT(*) as count FROM product_costs GROUP BY abc_classification ALLOW FILTERING")
        logger.info("\n🏆 Distribución por Clasificación ABC:")
        for row in result:
            logger.info(f"   • Clase {row.abc_classification}: {row.count} productos")
        
        logger.info("\n✅ Verificación completada exitosamente!")
        
    except Exception as e:
        logger.error(f"❌ Error durante la verificación: {e}")
        raise
    finally:
        if 'cluster' in locals():
            cluster.shutdown()

if __name__ == "__main__":
    verify_inventory_data() 