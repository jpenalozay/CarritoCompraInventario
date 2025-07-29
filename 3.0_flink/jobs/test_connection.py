#!/usr/bin/env python3

import json
import logging
from datetime import datetime
from cassandra.cluster import Cluster
import uuid

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_cassandra():
    """Test básico de conectividad a Cassandra"""
    try:
        logger.info("🔌 Conectando a Cassandra...")
        
        # Conectar a Cassandra
        cluster = Cluster(['cassandra'])
        session = cluster.connect()
        session.execute("USE ecommerce_analytics")
        logger.info("✅ Conectado a Cassandra")
        
        # Hacer inserción de prueba
        logger.info("💾 Probando inserción...")
        current_time = datetime.now()
        transaction_id = f"test_{int(current_time.timestamp())}"
        
        # Usar prepared statement correctamente
        insert_query = """
            INSERT INTO transactions (
                transaction_id, customer_id, country, total_amount, 
                quantity, description, unit_price, invoice_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Preparar la statement
        prepared = session.prepare(insert_query)
        
        values = (
            transaction_id,
            "test_customer", 
            "United Kingdom", 
            10.99,
            1, 
            "Test Product", 
            10.99, 
            current_time, 
            current_time
        )
        
        logger.info(f"Insertando: {values}")
        session.execute(prepared, values)
        logger.info("✅ Inserción exitosa!")
        
        # Verificar inserción
        logger.info("🔍 Verificando inserción...")
        select_query = "SELECT * FROM transactions WHERE transaction_id = ?"
        select_prepared = session.prepare(select_query)
        result = session.execute(select_prepared, (transaction_id,))
        for row in result:
            logger.info(f"Encontrado: {row}")
        
        logger.info("🎉 Test completado exitosamente!")
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_cassandra() 