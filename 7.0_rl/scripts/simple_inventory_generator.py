#!/usr/bin/env python3
"""
Script simplificado para generar datos de inventario para RL
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from cassandra.cluster import Cluster
import uuid
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("🚀 Iniciando generación simple de datos de inventario...")
        
        # Conectar a Cassandra
        cluster = Cluster(['cassandra'])
        session = cluster.connect('ecommerce_analytics')
        
        # Cargar Excel
        logger.info("📊 Cargando datos del Excel...")
        df = pd.read_excel('/tmp/online_retail.xlsx')
        logger.info(f"✅ Cargados {len(df)} registros")
        
        # Limpiar y procesar datos
        df = df.dropna(subset=['StockCode', 'Quantity', 'UnitPrice'])
        df = df[df['Quantity'] > 0]
        df = df[df['UnitPrice'] > 0]
        
        # Top 50 productos por revenue
        df['TotalRevenue'] = df['Quantity'] * df['UnitPrice']
        top_products = df.groupby('StockCode').agg({
            'Quantity': 'sum',
            'UnitPrice': 'mean',
            'TotalRevenue': 'sum',
            'Description': 'first'
        }).nlargest(50, 'TotalRevenue')
        
        logger.info(f"✅ Procesando {len(top_products)} productos top")
        
        # Insertar datos de inventario
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
                ordering_cost, waste_cost_rate, insurance_cost_rate, shelf_life_days,
                storage_requirements, abc_classification, profit_margin, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        count = 0
        for stock_code, row in top_products.iterrows():
            count += 1
            
            # Calcular stock basado en demanda
            daily_demand = max(1, int(row['Quantity'] / 365))  # Estimación de demanda diaria
            current_stock = daily_demand * random.randint(20, 60)  # 20-60 días de stock
            max_capacity = int(current_stock * random.uniform(1.5, 2.5))
            reorder_point = daily_demand * random.randint(10, 20)
            safety_stock = daily_demand * random.randint(5, 15)
            
            # Costos basados en precio
            procurement_cost = row['UnitPrice'] * random.uniform(0.5, 0.8)
            
            # Clasificación ABC simple
            if count <= 15:
                abc_class = 'A'
            elif count <= 35:
                abc_class = 'B'
            else:
                abc_class = 'C'
            
            # Insertar inventario
            session.execute(inventory_query, [
                str(stock_code),
                current_stock,
                max_capacity,
                reorder_point,
                safety_stock,
                f"WH001-A-{count:02d}",
                round(procurement_cost * 0.02, 2),
                datetime.now() - timedelta(days=random.randint(1, 30)),
                datetime.now(),
                'generator'
            ])
            
            # Insertar costos
            session.execute(cost_query, [
                str(stock_code),
                round(procurement_cost, 2),
                round(random.uniform(0.10, 0.20), 2),
                round(row['UnitPrice'] * random.uniform(0.1, 0.3), 2),
                round(random.uniform(50, 150), 2),
                round(random.uniform(0.02, 0.08), 3),
                round(random.uniform(0.005, 0.02), 3),
                random.randint(365, 1095),
                random.choice(['normal', 'climate_controlled', 'fragile']),
                abc_class,
                round(random.uniform(0.20, 0.50), 2),
                datetime.now()
            ])
            
            if count % 10 == 0:
                logger.info(f"✅ Procesados {count} productos...")
        
        # Insertar proveedores básicos
        logger.info("👥 Insertando proveedores...")
        suppliers = [
            ('SUP001', 'Global Supplies Ltd', 0.95),
            ('SUP002', 'Fashion Forward Inc', 0.88),
            ('SUP003', 'Electronics Pro', 0.92)
        ]
        
        supplier_query = """
            INSERT INTO suppliers (
                supplier_id, supplier_name, reliability_score, average_lead_time,
                lead_time_variance, minimum_order_quantity, payment_terms, active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        for supplier_id, name, reliability in suppliers:
            session.execute(supplier_query, [
                supplier_id,
                name,
                reliability,
                random.randint(5, 15),
                random.randint(1, 3),
                random.randint(50, 200),
                'NET30',
                True,
                datetime.now()
            ])
        
        # Insertar almacén
        logger.info("🏢 Configurando almacén...")
        warehouse_query = """
            INSERT INTO warehouse_config (
                warehouse_id, warehouse_name, location, total_capacity,
                current_utilization, operating_cost_per_day, storage_cost_per_unit,
                temperature_controlled, security_level, active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        session.execute(warehouse_query, [
            'WH001',
            'Central Warehouse',
            'London, UK',
            100000,
            0.75,
            500.0,
            0.025,
            True,
            'high',
            True
        ])
        
        logger.info("📊 RESUMEN:")
        logger.info(f"   📦 Productos: {count}")
        logger.info(f"   👥 Proveedores: {len(suppliers)}")
        logger.info(f"   🏢 Almacenes: 1")
        logger.info("✅ ¡Generación completada!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise
    finally:
        cluster.shutdown()

if __name__ == "__main__":
    main() 