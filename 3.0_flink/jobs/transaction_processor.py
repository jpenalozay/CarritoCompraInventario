#!/usr/bin/env python3

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.serialization import DeserializationSchema, SimpleStringSchema
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
from pyflink.common import WatermarkStrategy, Types
from pyflink.datastream.window import TumblingProcessingTimeWindows
from pyflink.common.time import Time
from pyflink.datastream.functions import ProcessWindowFunction, MapFunction, RuntimeContext, SinkFunction
from cassandra.cluster import Cluster
from redis import Redis
import json, pytz, uuid
from datetime import datetime
import io
from pathlib import Path

# ------------------------------------------------------------------
# Sink para Cassandra y Redis
# ------------------------------------------------------------------
class CassandraRedisSink(MapFunction):
    def __init__(self):
        self.cassandra_session = None
        self.redis_client = None
        self.insert_stmt = None
        
    def open(self, runtime_context: RuntimeContext):
        # Conectar a Cassandra
        cluster = Cluster(['cassandra'])
        self.cassandra_session = cluster.connect('ecommerce_analytics')
        
        # Preparar statement para Cassandra
        self.insert_stmt = self.cassandra_session.prepare("""
            INSERT INTO revenue_by_country_time (
                country, date_bucket, hour, timestamp, invoice_no,
                customer_id, revenue_gbp, revenue_usd, order_count,
                customer_count, avg_order_value, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)
        
        # Conectar a Redis
        self.redis_client = Redis(host='redis', port=6379, db=0)
        
    def close(self):
        if self.cassandra_session:
            self.cassandra_session.shutdown()
        if self.redis_client:
            self.redis_client.close()
            
    def map(self, value):
        try:
            # Extraer datos del valor
            country = value['country']
            timestamp = datetime.fromtimestamp(value['timestamp'])
            date_bucket = timestamp.date()
            hour = timestamp.hour
            
            # Insertar en Cassandra
            self.cassandra_session.execute(
                self.insert_stmt,
                (
                    country, date_bucket, hour, timestamp,
                    value['invoice_no'], value['customer_id'],
                    value['revenue_gbp'], value['revenue_usd'],
                    value['order_count'], value['customer_count'],
                    value['avg_order_value'], timestamp, timestamp
                )
            )
            
            # Actualizar contadores en Redis
            redis_key = f"revenue:{country}:{date_bucket}:{hour}"
            self.redis_client.hincrby(redis_key, "order_count", value['order_count'])
            self.redis_client.hincrbyfloat(redis_key, "revenue_gbp", float(value['revenue_gbp']))
            self.redis_client.hincrbyfloat(redis_key, "revenue_usd", float(value['revenue_usd']))
            self.redis_client.expire(redis_key, 86400 * 7)  # TTL de 7 días
            
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            
        return value  # Devolver el valor para mantener el flujo de datos

# ------------------------------------------------------------------
# Procesador de ventana (1-min)
# ------------------------------------------------------------------
class TransactionWindow(ProcessWindowFunction):
    def process(self, key, context, elements):
        try:
            total_revenue_gbp = 0.0
            order_count = 0
            customer_ids = set()

            for elem in elements:
                # Validar y convertir el total_amount
                try:
                    total_amount = float(elem.get('total_amount', 0))
                    if total_amount >= 0:  # Solo considerar montos positivos
                        total_revenue_gbp += total_amount
                        order_count += 1
                except (ValueError, TypeError):
                    print(f"Invalid total_amount in element: {elem}")
                    continue

                # Agregar customer_id si es válido
                customer_id = elem.get('customer_id')
                if customer_id and customer_id != 'UNKNOWN':
                    customer_ids.add(customer_id)

            # Solo procesar si hay datos válidos
            if order_count > 0:
                window_start = context.window().start  # epoch ms
                ts = datetime.fromtimestamp(window_start/1000, tz=pytz.UTC)
                date_bucket = ts.date()
                hour = ts.hour

                # Generar un customer_id aleatorio si no hay ninguno válido
                representative_customer_id = (
                    list(customer_ids)[0] if customer_ids 
                    else str(uuid.uuid4())
                )

                result = {
                    'country': key or 'UNKNOWN',
                    'date_bucket': date_bucket,
                    'hour': hour,
                    'timestamp': ts,
                    'invoice_no': str(uuid.uuid4()),
                    'customer_id': representative_customer_id,
                    'revenue_gbp': total_revenue_gbp,
                    'revenue_usd': total_revenue_gbp * 1.27,
                    'order_count': order_count,
                    'customer_count': len(customer_ids) or 1,  # Mínimo 1 cliente
                    'avg_order_value': total_revenue_gbp / order_count,
                    'created_at': ts,  # Usar la fecha del evento
                    'updated_at': ts   # Usar la fecha del evento
                }
                yield result
            else:
                print(f"No valid transactions in window for country: {key}")
        except Exception as e:
            print(f"Error procesando ventana: {str(e)}")
            # No yield None - mejor no enviar nada que enviar datos inválidos

# ------------------------------------------------------------------
# Función principal
# ------------------------------------------------------------------

def main():
    # Crear el entorno de ejecución
    env = StreamExecutionEnvironment.get_execution_environment()
    
    # Configurar el source de Kafka
    kafka_source = KafkaSource.builder() \
        .set_bootstrap_servers('kafka:9092') \
        .set_topics('ecommerce_transactions') \
        .set_group_id('flink-consumer-group') \
        .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
        .set_value_only_deserializer(SimpleStringSchema()) \
        .build()
    
    # Crear el stream de datos
    stream = env.from_source(
        source=kafka_source,
        watermark_strategy=WatermarkStrategy.no_watermarks(),
        source_name='Kafka Source'
    )
    
    # Procesar y agregar los datos
    stream \
        .map(lambda x: json.loads(x), output_type=Types.STRING()) \
        .key_by(lambda x: x['country']) \
        .window(TumblingProcessingTimeWindows.of(Time.minutes(5))) \
        .process(TransactionWindow()) \
        .map(CassandraRedisSink())
    
    # Ejecutar el job
    env.execute('Transaction Processor')

if __name__ == '__main__':
    main() 