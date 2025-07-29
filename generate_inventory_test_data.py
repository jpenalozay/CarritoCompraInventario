#!/usr/bin/env python3
"""
Script para generar datos de prueba para RL de inventario
"""
from cassandra.cluster import Cluster
import random
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 Generando datos de prueba para RL de inventario...")
    
    # Conectar a Cassandra
    cluster = Cluster(['localhost'], port=9042)
    session = cluster.connect('ecommerce_analytics')
    
    # Obtener productos únicos de las transacciones existentes
    logger.info("📊 Obteniendo productos únicos...")
    result = session.execute("""
        SELECT DISTINCT stock_code, country FROM transactions 
        WHERE stock_code IS NOT NULL 
        LIMIT 50
    """)
    
    products = [(row.stock_code, row.country) for row in result]
    logger.info(f"✅ Encontrados {len(products)} productos")
    
    # Insertar datos de inventario
    inventory_query = """
        INSERT INTO inventory_current (
            stock_code, current_stock, max_stock_capacity, reorder_point,
            safety_stock, location_id, storage_cost_per_unit, last_restock_date,
            last_updated, updated_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Insertar datos de costos
    cost_query = """
        INSERT INTO product_costs (
            stock_code, procurement_cost, holding_cost_rate, stockout_penalty,
            ordering_cost, abc_classification, profit_margin, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    for i, (stock_code, country) in enumerate(products):
        # Datos de inventario
        current_stock = random.randint(10, 500)
        max_capacity = current_stock * random.randint(2, 4)
        reorder_point = current_stock // 4
        safety_stock = current_stock // 8
        
        session.execute(inventory_query, [
            stock_code, current_stock, max_capacity, reorder_point,
            safety_stock, f"WH001-A-{i:02d}", 0.15, datetime.now(),
            datetime.now(), 'system'
        ])
        
        # Datos de costos
        abc_class = random.choice(['A', 'B', 'C'])
        procurement_cost = random.uniform(5.0, 50.0)
        holding_rate = random.uniform(0.10, 0.25)
        
        session.execute(cost_query, [
            stock_code, procurement_cost, holding_rate, 100.0,
            25.0, abc_class, 0.30, datetime.now()
        ])
    
    logger.info(f"✅ Insertados {len(products)} productos con datos de inventario")
    cluster.shutdown()

if __name__ == "__main__":
    main() 