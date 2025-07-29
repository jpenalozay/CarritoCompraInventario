#!/usr/bin/env python3

import json
import time
import logging
from kafka import KafkaConsumer
from cassandra.cluster import Cluster
from redis import Redis
from datetime import datetime
import uuid
import signal
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TransactionProcessor:
    def __init__(self):
        self.running = True
        self.consumer = None
        self.cassandra_session = None
        self.redis_client = None
        self.processed_count = 0
        
        # Configurar signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        logger.info("🛑 Received stop signal, shutting down gracefully...")
        self.running = False
        
    def connect_services(self):
        """Conectar a Kafka, Cassandra y Redis"""
        try:
            # Conectar a Kafka
            logger.info("🔌 Connecting to Kafka...")
            self.consumer = KafkaConsumer(
                'ecommerce_transactions',
                bootstrap_servers=['kafka:9092'],
                group_id='transaction-processor-v2',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                consumer_timeout_ms=1000
            )
            logger.info("✅ Connected to Kafka")
            
            # Conectar a Cassandra
            logger.info("🔌 Connecting to Cassandra...")
            cluster = Cluster(['cassandra'], port=9042)
            self.cassandra_session = cluster.connect('ecommerce_analytics')
            logger.info("✅ Connected to Cassandra")
            
            # Conectar a Redis
            logger.info("🔌 Connecting to Redis...")
            self.redis_client = Redis(
                host='redis', 
                port=6379, 
                db=0, 
                decode_responses=True,
                socket_timeout=5
            )
            self.redis_client.ping()
            logger.info("✅ Connected to Redis")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error connecting to services: {e}")
            return False
    
    def process_transaction(self, transaction):
        """Procesar una transacción"""
        try:
            # Extraer y validar datos
            country = transaction.get('country', 'UNKNOWN')
            total_amount = float(transaction.get('total_amount', 0))
            customer_id = str(transaction.get('customer_id', uuid.uuid4()))
            invoice_no = str(transaction.get('invoice_no', uuid.uuid4()))
            quantity = int(transaction.get('quantity', 1))
            
            if total_amount <= 0:
                return False
            
            # Insertar en Cassandra
            try:
                insert_query = """
                    INSERT INTO transactions (
                        invoice_no, customer_id, country, total_amount, 
                        quantity, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """
                
                self.cassandra_session.execute(
                    insert_query,
                    (invoice_no, customer_id, country, total_amount, quantity, datetime.now().isoformat())
                )
            except Exception as e:
                logger.warning(f"⚠️ Cassandra insert failed: {e}")
            
            # Actualizar métricas en Redis
            try:
                # Por país
                country_key = f"analytics:{country}"
                self.redis_client.hincrbyfloat(country_key, "revenue", total_amount)
                self.redis_client.hincrby(country_key, "orders", 1)
                self.redis_client.expire(country_key, 86400)
                
                # Global
                self.redis_client.hincrbyfloat("analytics:global", "total_revenue", total_amount)
                self.redis_client.hincrby("analytics:global", "total_orders", 1)
                
                # Por hora
                hour_key = f"analytics:hourly:{datetime.now().strftime('%Y-%m-%d-%H')}"
                self.redis_client.hincrbyfloat(hour_key, "revenue", total_amount)
                self.redis_client.hincrby(hour_key, "orders", 1)
                self.redis_client.expire(hour_key, 86400 * 7)  # 7 días
                
            except Exception as e:
                logger.warning(f"⚠️ Redis update failed: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing transaction: {e}")
            return False
    
    def run(self):
        """Ejecutar el procesador"""
        logger.info("🚀 Starting Kafka to Cassandra Processor...")
        
        if not self.connect_services():
            logger.error("❌ Failed to connect to services")
            return 1
        
        logger.info("🔄 Starting message consumption from Kafka...")
        logger.info("📊 Waiting for transactions...")
        
        try:
            while self.running:
                try:
                    # Obtener mensajes con timeout
                    message_batch = self.consumer.poll(timeout_ms=1000)
                    
                    if not message_batch:
                        continue
                    
                    # Procesar mensajes del batch
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            if not self.running:
                                break
                                
                            transaction = message.value
                            
                            if self.process_transaction(transaction):
                                self.processed_count += 1
                                
                                # Log cada 5 transacciones
                                if self.processed_count % 5 == 0:
                                    logger.info(f"📈 Processed {self.processed_count} transactions")
                            
                            # Pequeña pausa
                            time.sleep(0.05)
                    
                    # Commit manual
                    self.consumer.commit()
                    
                except Exception as e:
                    logger.error(f"❌ Error in processing loop: {e}")
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("⏹️ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
        finally:
            self.cleanup()
            
        logger.info(f"✅ Processor finished. Total processed: {self.processed_count}")
        return 0
    
    def cleanup(self):
        """Limpiar recursos"""
        logger.info("🧹 Cleaning up...")
        
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("✅ Kafka consumer closed")
            except:
                pass
                
        if self.cassandra_session:
            try:
                self.cassandra_session.shutdown()
                logger.info("✅ Cassandra session closed")
            except:
                pass
                
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("✅ Redis connection closed")
            except:
                pass

def main():
    processor = TransactionProcessor()
    exit_code = processor.run()
    sys.exit(exit_code)

if __name__ == '__main__':
    main() 