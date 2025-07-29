#!/usr/bin/env python3
"""
Script para verificar la conectividad con Cassandra
"""
import os
import sys
import time
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

def check_cassandra_connection():
    """Verifica la conexión con Cassandra"""
    cassandra_host = os.getenv('CASSANDRA_HOST', 'cassandra')
    cassandra_port = int(os.getenv('CASSANDRA_PORT', 9042))
    
    try:
        # Crear cluster
        cluster = Cluster([cassandra_host], port=cassandra_port)
        session = cluster.connect()
        
        # Ejecutar consulta simple
        result = session.execute("SELECT release_version FROM system.local")
        version = result.one()[0]
        
        print(f"✅ Cassandra está disponible - Versión: {version}")
        session.shutdown()
        cluster.shutdown()
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a Cassandra: {e}")
        return False

def check_redis_connection():
    """Verifica la conexión con Redis"""
    import redis
    
    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    
    try:
        r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        r.ping()
        print("✅ Redis está disponible")
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a Redis: {e}")
        return False

if __name__ == "__main__":
    # Verificar Cassandra
    cassandra_ready = False
    while not cassandra_ready:
        cassandra_ready = check_cassandra_connection()
        if not cassandra_ready:
            print("⏳ Esperando que Cassandra esté disponible...")
            time.sleep(5)
    
    # Verificar Redis
    redis_ready = False
    while not redis_ready:
        redis_ready = check_redis_connection()
        if not redis_ready:
            print("⏳ Esperando que Redis esté disponible...")
            time.sleep(5)
    
    print("✅ Todos los servicios están disponibles")
    sys.exit(0) 