#!/usr/bin/env python3
"""
Script simple para generar datos de inventario para RL
"""
from cassandra.cluster import Cluster
import random
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_inventory_data():
    """Generar datos de inventario basándose en productos existentes"""
    logger.info("🚀 Generando datos de inventario para RL...")
    
    # Conectar a Cassandra
    cassandra_host = os.getenv('CASSANDRA_HOST', 'cassandra')
    cluster = Cluster([cassandra_host], port=9042)
    session = cluster.connect('ecommerce_analytics')
    
    try:
        # Verificar si ya hay suficientes datos
        count_result = session.execute("SELECT COUNT(*) FROM inventory_current")
        current_count = count_result.one().count
        
        if current_count >= 20:
            logger.info(f"✅ Ya hay {current_count} productos con datos de inventario")
            return True
        
        # Obtener productos únicos de las transacciones
        logger.info("📊 Obteniendo productos únicos...")
        result = session.execute("""
            SELECT DISTINCT stock_code FROM transactions 
            WHERE stock_code IS NOT NULL 
            LIMIT 50
        """)
        
        products = [row.stock_code for row in result]
        logger.info(f"✅ Encontrados {len(products)} productos únicos")
        
        # Preparar queries
        inventory_query = """
            INSERT INTO inventory_current (
                stock_code, current_stock, max_stock_capacity, reorder_point,
                safety_stock, location_id, storage_cost_per_unit, last_restock_date,
                last_updated, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cost_query = """
            INSERT INTO product_costs (
                stock_code, procurement_cost, holding_cost_rate, stockout_penalty,
                ordering_cost, abc_classification, profit_margin, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Generar datos para cada producto
        for i, stock_code in enumerate(products):
            try:
                # Datos de inventario
                current_stock = random.randint(50, 300)
                max_capacity = current_stock * random.randint(2, 4)
                reorder_point = current_stock // 3
                safety_stock = current_stock // 6
                
                session.execute(inventory_query, [
                    stock_code, current_stock, max_capacity, reorder_point,
                    safety_stock, f"WH001-A-{i:02d}", 0.15, datetime.now(),
                    datetime.now(), 'rl_generator'
                ])
                
                # Datos de costos
                abc_class = random.choice(['A', 'A', 'B', 'B', 'B', 'C', 'C'])  # Más B y C
                procurement_cost = random.uniform(5.0, 50.0)
                holding_rate = random.uniform(0.10, 0.25)
                
                session.execute(cost_query, [
                    stock_code, procurement_cost, holding_rate, 150.0,
                    30.0, abc_class, random.uniform(0.20, 0.40), datetime.now()
                ])
                
                if (i + 1) % 10 == 0:
                    logger.info(f"📦 Procesados {i + 1}/{len(products)} productos")
                    
            except Exception as e:
                logger.warning(f"❌ Error procesando {stock_code}: {e}")
                continue
        
        logger.info(f"✅ Generación completada: {len(products)} productos con datos de inventario")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error generando datos: {e}")
        return False
    finally:
        cluster.shutdown()

if __name__ == "__main__":
    generate_inventory_data() 