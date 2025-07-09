import pandas as pd
import io
import json
from kafka import KafkaProducer
from kafka.errors import KafkaError
from datetime import datetime
import time
from pathlib import Path
import os
import sys
from typing import Dict, Any
import uuid

class TransactionProducer:
    def __init__(self, bootstrap_servers='kafka:9092', max_retries=5, retry_interval=5):
        self.bootstrap_servers = bootstrap_servers
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        
        # Ya no necesitamos cargar esquema Avro
        self.producer = self._connect_with_retry()
        
    def _connect_with_retry(self) -> KafkaProducer:
        """Intenta conectar a Kafka con reintentos"""
        retries = 0
        while retries < self.max_retries:
            try:
                print(f"Attempting to connect to Kafka (attempt {retries + 1}/{self.max_retries})...")
                producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    retries=5,
                    acks='all'
                )
                print("Successfully connected to Kafka!")
                return producer
            except KafkaError as e:
                retries += 1
                if retries == self.max_retries:
                    print(f"Failed to connect to Kafka after {self.max_retries} attempts. Error: {e}")
                    sys.exit(1)
                print(f"Failed to connect. Retrying in {self.retry_interval} seconds...")
                time.sleep(self.retry_interval)
        
        raise Exception("Failed to connect to Kafka")

    def serialize_avro(self, data: Dict[str, Any]) -> bytes:
        """Deprecated: kept to avoid attribute errors if referenced elsewhere."""
        return json.dumps(data).encode("utf-8")
    
    def process_row(self, row: pd.Series) -> Dict[str, Any]:
        try:
            # Validar datos requeridos
            if pd.isna(row['CustomerID']) or pd.isna(row['InvoiceNo']):
                raise ValueError("Missing required fields: CustomerID or InvoiceNo")
            
            # Convertir timestamp a epoch
            invoice_date = pd.to_datetime(row['InvoiceDate'])
            timestamp = int(invoice_date.timestamp())
            
            # Calcular monto total
            quantity = int(row['Quantity'])
            unit_price = float(row['UnitPrice'])
            
            # Solo validar que el precio no sea negativo
            if unit_price < 0:
                raise ValueError("Invalid price")
                
            total_amount = quantity * unit_price
            
            return {
                "invoice_no": str(row['InvoiceNo']),
                "stock_code": str(row['StockCode']),
                "description": str(row['Description']),
                "quantity": quantity,
                "invoice_date": timestamp,
                "unit_price": unit_price,
                "customer_id": str(row['CustomerID']),
                "country": str(row['Country']),
                "total_amount": total_amount
            }
        except Exception as e:
            print(f"Error processing row: {row.to_dict()}")
            print(f"Error details: {str(e)}")
            return None
    
    def send_transaction(self, transaction: Dict[str, Any]) -> bool:
        if not transaction:
            return False
            
        try:
            # Validar y completar datos faltantes
            if not self.validate_transaction(transaction):
                print(f"Error validating transaction: {transaction}")
                return False
                
            # Enviar al tópico general de transacciones
            topic = 'ecommerce_transactions'
            
            # Enviar mensaje con callback
            future = self.producer.send(topic, transaction)
            future.get(timeout=10)  # Esperar confirmación con timeout
            return True
            
        except Exception as e:
            print(f"Error sending transaction {transaction.get('invoice_no')}: {str(e)}")
            return False
    
    def process_dataset(self, excel_path: str, batch_size: int = 100) -> None:
        print(f"Processing dataset from: {excel_path}")
        
        if not os.path.exists(excel_path):
            print(f"Error: Dataset file not found at {excel_path}")
            sys.exit(1)
            
        try:
            # Leer todo el dataset y dividirlo manualmente en lotes
            df = pd.read_excel(excel_path)

            total_processed = 0
            total_failed = 0

            for start in range(0, len(df), batch_size):
                end = start + batch_size
                batch = df.iloc[start:end]

                batch_processed = 0
                batch_failed = 0

                for _, row in batch.iterrows():
                    try:
                        transaction = self.process_row(row)
                        if transaction and self.send_transaction(transaction):
                            batch_processed += 1
                        else:
                            batch_failed += 1

                        # Simular velocidad real de transacciones
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"Error processing row: {e}")
                        batch_failed += 1

                total_processed += batch_processed
                total_failed += batch_failed

                print(f"Processed batch: {batch_processed} successful, {batch_failed} failed")

                self.producer.flush()
            
            print(f"\nProcessing complete!")
            print(f"Total transactions processed: {total_processed}")
            print(f"Total transactions failed: {total_failed}")
            
        except Exception as e:
            print(f"Error processing dataset: {str(e)}")
            sys.exit(1)

    def validate_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Validate transaction data and fill missing fields."""
        if not transaction:
            return False
            
        # Convertir NaN a None para poder manejarlos mejor
        transaction = {k: None if pd.isna(v) else v for k, v in transaction.items()}
        
        # Generar un CustomerID aleatorio si no existe
        if transaction.get('CustomerID') is None:
            transaction['CustomerID'] = str(uuid.uuid4())
        
        # Generar un InvoiceNo aleatorio si no existe
        if transaction.get('InvoiceNo') is None:
            transaction['InvoiceNo'] = str(uuid.uuid4())
        
        # Convertir campos numéricos
        if transaction.get('Quantity') is not None:
            transaction['Quantity'] = int(transaction['Quantity'])
        if transaction.get('UnitPrice') is not None:
            transaction['UnitPrice'] = float(transaction['UnitPrice'])
        
        # Convertir timestamp
        if transaction.get('InvoiceDate') is not None:
            if isinstance(transaction['InvoiceDate'], pd.Timestamp):
                transaction['InvoiceDate'] = transaction['InvoiceDate'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                try:
                    transaction['InvoiceDate'] = datetime.strptime(str(transaction['InvoiceDate']), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    transaction['InvoiceDate'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return True

if __name__ == "__main__":
    # Configuración
    DATASET_PATH = os.getenv('DATASET_PATH', '/app/data/online_retail.xlsx')
    KAFKA_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    
    print(f"Starting producer with config:")
    print(f"- Dataset path: {DATASET_PATH}")
    print(f"- Kafka servers: {KAFKA_SERVERS}")
    
    # Iniciar productor
    producer = TransactionProducer(bootstrap_servers=KAFKA_SERVERS)
    
    # Procesar dataset
    producer.process_dataset(DATASET_PATH) 