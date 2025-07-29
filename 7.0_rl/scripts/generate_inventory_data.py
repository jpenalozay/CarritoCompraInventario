#!/usr/bin/env python3
"""
Script para generar datos de inventario para RL basándose en el Excel de retail existente
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import uuid
import json
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InventoryDataGenerator:
    def __init__(self):
        self.excel_path = 'data/online_retail.xlsx'
        self.cassandra_host = os.getenv('CASSANDRA_HOST', 'cassandra')
        self.cassandra_port = int(os.getenv('CASSANDRA_PORT', 9042))
        
        # Conectar a Cassandra
        self.cluster = Cluster([self.cassandra_host], port=self.cassandra_port)
        self.session = self.cluster.connect('ecommerce_analytics')
        
        # Categorías de productos con características típicas
        self.product_categories = {
            'Electronics': {
                'shelf_life_days': 1095,  # 3 años
                'holding_cost_rate': 0.15,
                'profit_margin': 0.25,
                'lead_time_range': (5, 15),
                'min_order_multiplier': 50
            },
            'Home & Kitchen': {
                'shelf_life_days': 730,  # 2 años
                'holding_cost_rate': 0.12,
                'profit_margin': 0.35,
                'lead_time_range': (3, 10),
                'min_order_multiplier': 20
            },
            'Fashion': {
                'shelf_life_days': 365,  # 1 año (temporadas)
                'holding_cost_rate': 0.20,
                'profit_margin': 0.45,
                'lead_time_range': (7, 21),
                'min_order_multiplier': 30
            },
            'Books': {
                'shelf_life_days': 1825,  # 5 años
                'holding_cost_rate': 0.08,
                'profit_margin': 0.40,
                'lead_time_range': (2, 7),
                'min_order_multiplier': 10
            },
            'Sports': {
                'shelf_life_days': 1095,  # 3 años
                'holding_cost_rate': 0.14,
                'profit_margin': 0.30,
                'lead_time_range': (5, 14),
                'min_order_multiplier': 25
            },
            'Beauty': {
                'shelf_life_days': 1095,  # 3 años
                'holding_cost_rate': 0.18,
                'profit_margin': 0.50,
                'lead_time_range': (4, 12),
                'min_order_multiplier': 15
            },
            'Default': {
                'shelf_life_days': 730,
                'holding_cost_rate': 0.15,
                'profit_margin': 0.30,
                'lead_time_range': (5, 14),
                'min_order_multiplier': 20
            }
        }
        
        # Proveedores ficticios pero realistas
        self.suppliers = [
            {
                'supplier_id': 'SUP001',
                'supplier_name': 'Global Electronics Ltd',
                'reliability_score': 0.95,
                'payment_terms': 'NET30',
                'specialties': ['Electronics', 'Home & Kitchen']
            },
            {
                'supplier_id': 'SUP002', 
                'supplier_name': 'Fashion Forward Inc',
                'reliability_score': 0.88,
                'payment_terms': 'NET45',
                'specialties': ['Fashion', 'Beauty']
            },
            {
                'supplier_id': 'SUP003',
                'supplier_name': 'Book Distributors Co',
                'reliability_score': 0.92,
                'payment_terms': 'NET15',
                'specialties': ['Books']
            },
            {
                'supplier_id': 'SUP004',
                'supplier_name': 'Sports Equipment Pro',
                'reliability_score': 0.90,
                'payment_terms': 'NET30',
                'specialties': ['Sports', 'Home & Kitchen']
            },
            {
                'supplier_id': 'SUP005',
                'supplier_name': 'Universal Supplies',
                'reliability_score': 0.85,
                'payment_terms': 'NET60',
                'specialties': ['Default']  # Proveedor genérico
            }
        ]

    def categorize_product(self, description):
        """Categorizar producto basándose en la descripción"""
        if not description or pd.isna(description):
            return 'Default'
        
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['phone', 'laptop', 'electronic', 'computer', 'cable', 'charger', 'headphone']):
            return 'Electronics'
        elif any(word in description_lower for word in ['kitchen', 'home', 'furniture', 'decor', 'appliance']):
            return 'Home & Kitchen'
        elif any(word in description_lower for word in ['shirt', 'dress', 'fashion', 'clothing', 'wear', 'bag', 'shoe']):
            return 'Fashion'
        elif any(word in description_lower for word in ['book', 'journal', 'diary', 'notebook', 'paper']):
            return 'Books'
        elif any(word in description_lower for word in ['sport', 'game', 'ball', 'fitness', 'outdoor']):
            return 'Sports'
        elif any(word in description_lower for word in ['beauty', 'cosmetic', 'perfume', 'cream', 'lotion']):
            return 'Beauty'
        else:
            return 'Default'

    def calculate_abc_classification(self, revenue_data):
        """Clasificación ABC basada en el revenue de productos"""
        # Ordenar por revenue descendente
        sorted_data = revenue_data.sort_values('total_revenue', ascending=False).reset_index(drop=True)
        
        # Calcular revenue acumulativo
        sorted_data['cumulative_revenue'] = sorted_data['total_revenue'].cumsum()
        total_revenue = sorted_data['total_revenue'].sum()
        sorted_data['cumulative_percentage'] = sorted_data['cumulative_revenue'] / total_revenue * 100
        
        # Asignar clasificación ABC
        conditions = [
            sorted_data['cumulative_percentage'] <= 70,
            sorted_data['cumulative_percentage'] <= 90,
            sorted_data['cumulative_percentage'] <= 100
        ]
        choices = ['A', 'B', 'C']
        sorted_data['abc_classification'] = np.select(conditions, choices, default='C')
        
        return dict(zip(sorted_data['stock_code'], sorted_data['abc_classification']))

    def load_and_analyze_excel_data(self):
        """Cargar y analizar datos del Excel"""
        logger.info("📊 Cargando datos del Excel...")
        
        try:
            # Cargar Excel
            df = pd.read_excel(self.excel_path)
            logger.info(f"✅ Cargados {len(df)} registros del Excel")
            
            # Limpiar datos
            df = df.dropna(subset=['StockCode', 'Quantity', 'UnitPrice'])
            df = df[df['Quantity'] > 0]  # Solo ventas positivas
            df = df[df['UnitPrice'] > 0]  # Solo precios positivos
            
            # Calcular revenue total por producto
            df['TotalRevenue'] = df['Quantity'] * df['UnitPrice']
            
            # Agregar por producto
            product_summary = df.groupby(['StockCode', 'Description']).agg({
                'Quantity': ['sum', 'mean', 'std', 'count'],
                'UnitPrice': 'mean',
                'TotalRevenue': 'sum',
                'InvoiceDate': ['min', 'max']
            }).round(2)
            
            # Aplanar columnas
            product_summary.columns = ['_'.join(col).strip() for col in product_summary.columns]
            product_summary = product_summary.reset_index()
            
            # Renombrar columnas
            product_summary = product_summary.rename(columns={
                'Quantity_sum': 'total_quantity_sold',
                'Quantity_mean': 'avg_quantity_per_order',
                'Quantity_std': 'quantity_volatility',
                'Quantity_count': 'number_of_orders',
                'UnitPrice_mean': 'avg_unit_price',
                'TotalRevenue_sum': 'total_revenue',
                'InvoiceDate_min': 'first_sale_date',
                'InvoiceDate_max': 'last_sale_date'
            })
            
            # Categorizar productos
            product_summary['category'] = product_summary['Description'].apply(self.categorize_product)
            
            # Calcular clasificación ABC
            abc_classification = self.calculate_abc_classification(product_summary)
            product_summary['abc_classification'] = product_summary['StockCode'].map(abc_classification)
            
            # Calcular estadísticas de demanda
            product_summary['demand_frequency'] = product_summary['total_quantity_sold'] / product_summary['number_of_orders']
            product_summary['sales_duration_days'] = (
                pd.to_datetime(product_summary['last_sale_date']) - 
                pd.to_datetime(product_summary['first_sale_date'])
            ).dt.days + 1
            
            product_summary['daily_demand_avg'] = (
                product_summary['total_quantity_sold'] / product_summary['sales_duration_days']
            ).fillna(0)
            
            logger.info(f"✅ Procesados {len(product_summary)} productos únicos")
            logger.info(f"📈 Categorías encontradas: {product_summary['category'].value_counts().to_dict()}")
            logger.info(f"🏆 Clasificación ABC: {product_summary['abc_classification'].value_counts().to_dict()}")
            
            return product_summary
            
        except Exception as e:
            logger.error(f"❌ Error cargando Excel: {e}")
            raise

    def generate_inventory_data(self, product_summary):
        """Generar datos de inventario basándose en el análisis"""
        logger.info("🏭 Generando datos de inventario...")
        
        inventory_data = []
        cost_data = []
        supplier_data = []
        demand_metrics = []
        
        for _, product in product_summary.iterrows():
            stock_code = product['StockCode']
            category = product['category']
            abc_class = product['abc_classification']
            daily_demand = product['daily_demand_avg']
            
            # Obtener características de la categoría
            cat_config = self.product_categories.get(category, self.product_categories['Default'])
            
            # Calcular stock actual basado en demanda histórica
            # Regla: mantener entre 15-45 días de inventario según clasificación ABC
            if abc_class == 'A':
                days_of_supply_target = random.uniform(30, 45)  # Más stock para productos A
            elif abc_class == 'B':
                days_of_supply_target = random.uniform(20, 35)
            else:  # Clase C
                days_of_supply_target = random.uniform(15, 25)
                
            current_stock = max(int(daily_demand * days_of_supply_target), 1)
            
            # Calcular capacidades y puntos de reorden
            max_capacity = int(current_stock * random.uniform(1.5, 3.0))
            safety_stock = max(int(daily_demand * random.uniform(5, 10)), 1)
            reorder_point = max(int(daily_demand * random.uniform(10, 20)), safety_stock + 1)
            
            # Seleccionar proveedor
            suitable_suppliers = [s for s in self.suppliers 
                                if category in s['specialties'] or 'Default' in s['specialties']]
            supplier = random.choice(suitable_suppliers)
            
            # Calcular costos
            base_cost = product['avg_unit_price'] * random.uniform(0.4, 0.7)  # 40-70% del precio de venta
            lead_time = random.randint(*cat_config['lead_time_range'])
            
            # Datos de inventario actual
            inventory_record = {
                'stock_code': stock_code,
                'current_stock': current_stock,
                'max_stock_capacity': max_capacity,
                'reorder_point': reorder_point,
                'safety_stock': safety_stock,
                'location_id': f"WH001-{random.choice(['A', 'B', 'C'])}-{random.randint(1,50):02d}",
                'storage_cost_per_unit': round(base_cost * 0.02, 4),  # 2% del costo como almacenamiento
                'last_restock_date': datetime.now() - timedelta(days=random.randint(1, 30)),
                'last_updated': datetime.now(),
                'updated_by': 'inventory_generator'
            }
            inventory_data.append(inventory_record)
            
            # Datos de costos
            cost_record = {
                'stock_code': stock_code,
                'procurement_cost': round(base_cost, 2),
                'holding_cost_rate': cat_config['holding_cost_rate'],
                'stockout_penalty': round(product['avg_unit_price'] * random.uniform(0.1, 0.3), 2),
                'ordering_cost': round(random.uniform(50, 200), 2),
                'waste_cost_rate': random.uniform(0.02, 0.08),
                'insurance_cost_rate': random.uniform(0.005, 0.02),
                'shelf_life_days': cat_config['shelf_life_days'],
                'storage_requirements': random.choice(['normal', 'climate_controlled', 'fragile']),
                'abc_classification': abc_class,
                'profit_margin': cat_config['profit_margin'],
                'updated_at': datetime.now()
            }
            cost_data.append(cost_record)
            
            # Relación producto-proveedor
            supplier_record = {
                'stock_code': stock_code,
                'supplier_id': supplier['supplier_id'],
                'procurement_cost': round(base_cost, 2),
                'lead_time_days': lead_time,
                'minimum_quantity': max(int(daily_demand * cat_config['min_order_multiplier']), 10),
                'bulk_discounts': {
                    '100': 0.02,  # 2% descuento por 100+ unidades
                    '500': 0.05,  # 5% descuento por 500+ unidades
                    '1000': 0.08  # 8% descuento por 1000+ unidades
                },
                'is_primary': True,
                'contract_start_date': datetime.now() - timedelta(days=random.randint(30, 365)),
                'contract_end_date': datetime.now() + timedelta(days=random.randint(90, 730))
            }
            supplier_data.append(supplier_record)
            
            # Métricas de demanda
            demand_record = {
                'stock_code': stock_code,
                'date_calculated': datetime.now().date(),
                'daily_demand_avg': round(daily_demand, 2),
                'demand_variance': round(product.get('quantity_volatility', 1.0) ** 2, 2),
                'demand_trend': round(random.uniform(-0.1, 0.1), 3),  # -10% a +10% tendencia
                'seasonal_factor': round(random.uniform(0.8, 1.2), 2),
                'day_of_week_factors': {
                    'monday': round(random.uniform(0.8, 1.1), 2),
                    'tuesday': round(random.uniform(0.9, 1.1), 2),
                    'wednesday': round(random.uniform(0.9, 1.2), 2),
                    'thursday': round(random.uniform(0.9, 1.2), 2),
                    'friday': round(random.uniform(1.0, 1.3), 2),
                    'saturday': round(random.uniform(1.1, 1.4), 2),
                    'sunday': round(random.uniform(0.7, 1.0), 2)
                },
                'velocity_category': abc_class,
                'forecast_accuracy': round(random.uniform(0.7, 0.95), 2),
                'calculation_method': 'historical_analysis'
            }
            demand_metrics.append(demand_record)
        
        logger.info(f"✅ Generados datos para {len(inventory_data)} productos")
        return inventory_data, cost_data, supplier_data, demand_metrics

    def insert_suppliers(self):
        """Insertar datos de proveedores"""
        logger.info("👥 Insertando proveedores...")
        
        for supplier in self.suppliers:
            # Convertir especialidades en metadata
            bulk_discounts = {
                '100': 0.02,
                '500': 0.05,
                '1000': 0.08
            }
            
            contact_info = {
                'email': f"contact@{supplier['supplier_name'].lower().replace(' ', '').replace(',', '')}.com",
                'phone': f"+44-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
            }
            
            insert_query = """
                INSERT INTO suppliers (
                    supplier_id, supplier_name, reliability_score, average_lead_time,
                    lead_time_variance, minimum_order_quantity, bulk_discount_tiers,
                    payment_terms, contact_info, active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.session.execute(insert_query, [
                supplier['supplier_id'],
                supplier['supplier_name'],
                supplier['reliability_score'],
                random.randint(5, 15),  # average_lead_time
                random.randint(1, 3),   # lead_time_variance
                random.randint(50, 200),  # minimum_order_quantity
                bulk_discounts,
                supplier['payment_terms'],
                contact_info,
                True,
                datetime.now()
            ])
        
        logger.info(f"✅ Insertados {len(self.suppliers)} proveedores")

    def insert_inventory_data(self, inventory_data, cost_data, supplier_data, demand_metrics):
        """Insertar todos los datos de inventario en Cassandra"""
        logger.info("💾 Insertando datos en Cassandra...")
        
        # Insertar datos de inventario actual
        inventory_query = """
            INSERT INTO inventory_current (
                stock_code, current_stock, max_stock_capacity, reorder_point,
                safety_stock, location_id, storage_cost_per_unit, last_restock_date,
                last_updated, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        for record in inventory_data:
            self.session.execute(inventory_query, [
                record['stock_code'], record['current_stock'], record['max_stock_capacity'],
                record['reorder_point'], record['safety_stock'], record['location_id'],
                record['storage_cost_per_unit'], record['last_restock_date'],
                record['last_updated'], record['updated_by']
            ])
        
        logger.info(f"✅ Insertados {len(inventory_data)} registros de inventario")
        
        # Insertar datos de costos
        cost_query = """
            INSERT INTO product_costs (
                stock_code, procurement_cost, holding_cost_rate, stockout_penalty,
                ordering_cost, waste_cost_rate, insurance_cost_rate, shelf_life_days,
                storage_requirements, abc_classification, profit_margin, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        for record in cost_data:
            self.session.execute(cost_query, [
                record['stock_code'], record['procurement_cost'], record['holding_cost_rate'],
                record['stockout_penalty'], record['ordering_cost'], record['waste_cost_rate'],
                record['insurance_cost_rate'], record['shelf_life_days'], record['storage_requirements'],
                record['abc_classification'], record['profit_margin'], record['updated_at']
            ])
        
        logger.info(f"✅ Insertados {len(cost_data)} registros de costos")
        
        # Insertar relaciones producto-proveedor
        supplier_query = """
            INSERT INTO product_suppliers (
                stock_code, supplier_id, procurement_cost, lead_time_days,
                minimum_quantity, bulk_discounts, is_primary, contract_start_date,
                contract_end_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        for record in supplier_data:
            self.session.execute(supplier_query, [
                record['stock_code'], record['supplier_id'], record['procurement_cost'],
                record['lead_time_days'], record['minimum_quantity'], record['bulk_discounts'],
                record['is_primary'], record['contract_start_date'], record['contract_end_date']
            ])
        
        logger.info(f"✅ Insertados {len(supplier_data)} registros de proveedores")
        
        # Insertar métricas de demanda
        demand_query = """
            INSERT INTO demand_metrics (
                stock_code, date_calculated, daily_demand_avg, demand_variance,
                demand_trend, seasonal_factor, day_of_week_factors, velocity_category,
                forecast_accuracy, calculation_method
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        for record in demand_metrics:
            self.session.execute(demand_query, [
                record['stock_code'], record['date_calculated'], record['daily_demand_avg'],
                record['demand_variance'], record['demand_trend'], record['seasonal_factor'],
                record['day_of_week_factors'], record['velocity_category'], record['forecast_accuracy'],
                record['calculation_method']
            ])
        
        logger.info(f"✅ Insertados {len(demand_metrics)} registros de métricas de demanda")

    def generate_sample_events(self, product_summary, num_events=100):
        """Generar eventos de inventario de ejemplo"""
        logger.info(f"📝 Generando {num_events} eventos de inventario...")
        
        event_types = ['reorder', 'adjustment', 'shrinkage', 'receipt']
        event_weights = [0.4, 0.2, 0.1, 0.3]  # Probabilidades
        
        products = product_summary['StockCode'].tolist()
        
        for _ in range(num_events):
            stock_code = random.choice(products)
            event_type = random.choices(event_types, weights=event_weights)[0]
            event_timestamp = datetime.now() - timedelta(days=random.randint(1, 90))
            
            # Simular cambios de cantidad según el tipo de evento
            if event_type == 'reorder':
                quantity_change = random.randint(50, 500)
                reason = 'Automatic reorder triggered'
                supplier_id = random.choice([s['supplier_id'] for s in self.suppliers])
                cost = quantity_change * random.uniform(2.0, 20.0)
            elif event_type == 'receipt':
                quantity_change = random.randint(20, 300)
                reason = 'Supplier delivery received'
                supplier_id = random.choice([s['supplier_id'] for s in self.suppliers])
                cost = quantity_change * random.uniform(2.0, 20.0)
            elif event_type == 'adjustment':
                quantity_change = random.randint(-50, 50)
                reason = 'Inventory count adjustment'
                supplier_id = None
                cost = 0.0
            else:  # shrinkage
                quantity_change = -random.randint(1, 20)
                reason = 'Product damage/theft'
                supplier_id = None
                cost = abs(quantity_change) * random.uniform(2.0, 20.0)
            
            # Simular stock anterior y nuevo
            previous_stock = random.randint(10, 200)
            new_stock = max(0, previous_stock + quantity_change)
            
            event_query = """
                INSERT INTO inventory_events (
                    event_id, stock_code, event_type, event_timestamp, quantity_change,
                    previous_stock, new_stock, supplier_id, cost, reason, created_by, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            metadata = {
                'generated': 'true',
                'batch_id': 'initial_load',
                'category': 'historical_simulation'
            }
            
            self.session.execute(event_query, [
                uuid.uuid4(), stock_code, event_type, event_timestamp, quantity_change,
                previous_stock, new_stock, supplier_id, cost, reason, 'data_generator', metadata
            ])
        
        logger.info(f"✅ Generados {num_events} eventos de inventario")

    def generate_warehouse_data(self):
        """Generar datos de almacén y ubicaciones"""
        logger.info("🏢 Generando datos de almacén...")
        
        # Insertar configuración de almacén
        warehouse_query = """
            INSERT INTO warehouse_config (
                warehouse_id, warehouse_name, location, total_capacity,
                current_utilization, operating_cost_per_day, storage_cost_per_unit,
                temperature_controlled, security_level, manager_contact, active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        manager_contact = {
            'name': 'John Smith',
            'email': 'john.smith@warehouse.com',
            'phone': '+44-207-123-4567',
            'shift': 'day'
        }
        
        self.session.execute(warehouse_query, [
            'WH001', 'Central London Warehouse', 'London, UK', 100000,
            0.75, 850.0, 0.025, True, 'high', manager_contact, True
        ])
        
        logger.info("✅ Configuración de almacén insertada")

    def run(self):
        """Ejecutar todo el proceso de generación de datos"""
        try:
            logger.info("🚀 Iniciando generación de datos de inventario para RL...")
            
            # 1. Cargar y analizar datos del Excel
            product_summary = self.load_and_analyze_excel_data()
            
            # 2. Generar datos de inventario
            inventory_data, cost_data, supplier_data, demand_metrics = self.generate_inventory_data(product_summary)
            
            # 3. Insertar proveedores
            self.insert_suppliers()
            
            # 4. Insertar configuración de almacén
            self.generate_warehouse_data()
            
            # 5. Insertar todos los datos
            self.insert_inventory_data(inventory_data, cost_data, supplier_data, demand_metrics)
            
            # 6. Generar eventos de ejemplo
            self.generate_sample_events(product_summary, num_events=200)
            
            # 7. Mostrar estadísticas finales
            logger.info("📊 RESUMEN DE DATOS GENERADOS:")
            logger.info(f"   📦 Productos con inventario: {len(inventory_data)}")
            logger.info(f"   👥 Proveedores: {len(self.suppliers)}")
            logger.info(f"   💰 Registros de costos: {len(cost_data)}")
            logger.info(f"   📈 Métricas de demanda: {len(demand_metrics)}")
            logger.info(f"   📝 Eventos históricos: 200")
            logger.info(f"   🏢 Almacenes configurados: 1")
            
            logger.info("✅ ¡Generación de datos de inventario completada exitosamente!")
            
        except Exception as e:
            logger.error(f"❌ Error durante la generación: {e}")
            raise
        finally:
            if hasattr(self, 'cluster'):
                self.cluster.shutdown()

if __name__ == "__main__":
    generator = InventoryDataGenerator()
    generator.run() 