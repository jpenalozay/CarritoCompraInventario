#!/usr/bin/env python3

import json
import time
import logging
import sys
import uuid
import signal
import threading
from datetime import datetime
from kafka import KafkaConsumer
from cassandra.cluster import Cluster
import redis

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('StreamProcessor')

class ECommerceStreamProcessor:
    def __init__(self):
        self.running = True
        self.consumer = None
        self.cassandra_session = None
        self.redis_client = None
        self.processed_count = 0
        self.error_count = 0
        
        # Configurar signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        logger.info("🛑 Shutdown signal received, stopping gracefully...")
        self.running = False
        
    def connect_to_services(self):
        """Conectar a Kafka, Cassandra y Redis"""
        try:
            # Conexión a Kafka
            self.consumer = KafkaConsumer(
                'ecommerce_transactions',
                bootstrap_servers=['kafka:9092'],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='flink_stream_processor',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logger.info("✅ Connected to Kafka")
            
            # Conexión a Cassandra
            cluster = Cluster(['cassandra'])
            self.cassandra_session = cluster.connect()
            self.cassandra_session.execute("USE ecommerce_analytics")
            logger.info("✅ Connected to Cassandra (ecommerce_analytics)")
            
            # Preparar statement de Cassandra
            insert_query = """
                INSERT INTO transactions (
                    invoice_no, stock_code, customer_id, country, total_amount, 
                    quantity, description, unit_price, invoice_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.prepared_statement = self.cassandra_session.prepare(insert_query)
            logger.info("✅ Prepared Cassandra statement")
            
            # Conexión a Redis
            self.redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            logger.info("✅ Connected to Redis")
            
            logger.info("✅ All services connected successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to services: {e}")
            return False
    
    def process_transaction(self, transaction_data):
        """Procesar una transacción individual"""
        try:
            # Extraer y validar datos
            country = str(transaction_data.get('country', 'UNKNOWN')).strip()
            total_amount = float(transaction_data.get('total_amount', 0))
            customer_id = str(transaction_data.get('customer_id', str(uuid.uuid4())))
            invoice_no = str(transaction_data.get('invoice_no', str(uuid.uuid4())))
            stock_code = str(transaction_data.get('stock_code', str(uuid.uuid4())))
            quantity = int(transaction_data.get('quantity', 1))
            description = str(transaction_data.get('description', 'Unknown Product'))
            
            # Usar la fecha original del invoice si está disponible
            original_date = transaction_data.get('invoice_date')
            logger.debug(f"🔍 Raw invoice_date from Kafka: {original_date}, type: {type(original_date)}")
            
            if original_date:
                try:
                    # Si es un timestamp Unix (número)
                    if isinstance(original_date, (int, float)):
                        invoice_date = datetime.fromtimestamp(original_date)
                        logger.debug(f"✅ Parsed Unix timestamp: {invoice_date}")
                    else:
                        # Si es un string, usar dateutil parser
                        from dateutil import parser
                        invoice_date = parser.parse(str(original_date))
                        logger.debug(f"✅ Parsed string date: {invoice_date}")
                except Exception as parse_error:
                    logger.warning(f"⚠️ Failed to parse invoice_date '{original_date}': {parse_error}")
                    invoice_date = datetime.now()
            else:
                logger.debug("⚠️ No invoice_date found, using current time")
                invoice_date = datetime.now()
            
            current_time = datetime.now()  # Solo para created_at
            
            # Validar que el monto sea válido
            if total_amount <= 0:
                logger.debug(f"Skipping transaction with invalid amount: {total_amount}")
                return False
            
            # 1. Insertar en Cassandra
            try:
                unit_price = total_amount / quantity if quantity > 0 else 0
                transaction_id = f"{invoice_no}_{customer_id}_{int(current_time.timestamp())}"
                
                # Preparar los valores usando la fecha original
                values = (
                    invoice_no,
                    stock_code,
                    customer_id, 
                    country, 
                    float(total_amount),
                    int(quantity), 
                    description, 
                    float(unit_price), 
                    invoice_date,  # Usar fecha original aquí
                    current_time   # Solo created_at usa tiempo actual
                )
                
                logger.debug(f"🔍 Inserting: {values}")
                self.cassandra_session.execute(self.prepared_statement, values)
                logger.debug(f"💾 Saved to Cassandra: {transaction_id}")
                
            except Exception as e:
                logger.error(f"⚠️ Cassandra insert failed for {invoice_no}: {e}")
                logger.error(f"   Data: {transaction_data}")
                return False
            
            # 2. Actualizar métricas en Redis usando fecha original
            try:
                pipe = self.redis_client.pipeline()
                
                # Métricas por país
                country_key = f"analytics:country:{country}"
                pipe.hincrbyfloat(country_key, "revenue", total_amount)
                pipe.hincrby(country_key, "orders", 1)
                pipe.expire(country_key, 86400)  # 24 horas
                
                # Métricas globales
                pipe.hincrbyfloat("analytics:global:revenue", "total", total_amount)
                pipe.hincrby("analytics:global:orders", "total", 1)
                
                # Métricas por hora usando fecha original
                hour_key = f"analytics:hourly:{invoice_date.strftime('%Y-%m-%d-%H')}"
                pipe.hincrbyfloat(hour_key, "revenue", total_amount)
                pipe.hincrby(hour_key, "orders", 1)
                pipe.expire(hour_key, 172800)  # 48 horas
                
                pipe.execute()
                logger.debug(f"📊 Updated Redis metrics for {country} on {invoice_date.date()}")
                
            except Exception as e:
                logger.warning(f"⚠️ Redis update failed: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process transaction: {e}")
            logger.error(f"   Transaction data: {transaction_data}")
            return False
    
    def start_processing(self):
        """Iniciar el procesamiento de transacciones"""
        logger.info("🚀 Starting E-commerce Stream Processor...")
        
        if not self.connect_to_services():
            logger.error("❌ Failed to connect to required services")
            return 1
        
        logger.info("🔄 Starting message consumption from Kafka...")
        logger.info("📊 Processing transactions in real-time...")
        
        try:
            # Loop principal de procesamiento
            consecutive_empty_polls = 0
            max_empty_polls = 10
            
            while self.running:
                try:
                    # Obtener mensajes de Kafka
                    message_batch = self.consumer.poll(timeout_ms=2000)
                    
                    if not message_batch:
                        consecutive_empty_polls += 1
                        if consecutive_empty_polls >= max_empty_polls:
                            logger.info("📭 No new messages for a while, continuing to poll...")
                            consecutive_empty_polls = 0
                        continue
                    
                    consecutive_empty_polls = 0
                    
                    # Procesar cada mensaje en el batch
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            if not self.running:
                                break
                                
                            transaction = message.value
                            logger.info(f"🔍 Processing message: {transaction}")
                            
                            if self.process_transaction(transaction):
                                self.processed_count += 1
                                logger.info(f"✅ Successfully processed transaction {self.processed_count}")
                                
                                # Log progreso cada 10 transacciones
                                if self.processed_count % 10 == 0:
                                    logger.info(
                                        f"📈 Processed: {self.processed_count} transactions, "
                                        f"Errors: {self.error_count}"
                                    )
                            else:
                                self.error_count += 1
                                logger.error(f"❌ Failed to process transaction: {transaction}")
                            
                            # Pequeña pausa para no saturar
                            time.sleep(0.02)
                    
                    # Commit manual de offsets
                    try:
                        self.consumer.commit()
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to commit offsets: {e}")
                        
                except Exception as e:
                    logger.error(f"❌ Error in processing loop: {e}")
                    time.sleep(5)  # Pausa antes de reintentar
                    
        except KeyboardInterrupt:
            logger.info("⏹️ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Fatal error in main loop: {e}")
        finally:
            self.cleanup()
            
        logger.info(
            f"✅ Stream processor finished. "
            f"Total processed: {self.processed_count}, "
            f"Errors: {self.error_count}"
        )
        return 0
    
    def cleanup(self):
        """Limpiar todos los recursos"""
        logger.info("🧹 Cleaning up resources...")
        
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("✅ Kafka consumer closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing Kafka consumer: {e}")
                
        if self.cassandra_session:
            try:
                self.cassandra_session.shutdown()
                logger.info("✅ Cassandra session closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing Cassandra session: {e}")
                
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("✅ Redis connection closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing Redis connection: {e}")

def main():
    """Función principal"""
    logger.info("🎯 E-commerce Stream Processor Starting...")
    
    processor = ECommerceStreamProcessor()
    
    try:
        exit_code = processor.start_processing()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 