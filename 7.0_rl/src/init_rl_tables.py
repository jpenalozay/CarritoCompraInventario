#!/usr/bin/env python3
"""
Script para inicializar las tablas de Reinforcement Learning en Cassandra
"""
import os
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from datetime import datetime

def init_rl_tables():
    """Inicializa las tablas necesarias para el componente RL"""
    cassandra_host = os.getenv('CASSANDRA_HOST', 'cassandra')
    cassandra_port = int(os.getenv('CASSANDRA_PORT', 9042))
    
    try:
        # Conectar a Cassandra
        cluster = Cluster([cassandra_host], port=cassandra_port)
        session = cluster.connect()
        
        # Crear keyspace si no existe
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS ecommerce_analytics 
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
        """)
        
        # Usar el keyspace
        session.set_keyspace('ecommerce_analytics')
        
        # Tabla para estados del agente RL
        session.execute("""
            CREATE TABLE IF NOT EXISTS rl_states (
                user_id text,
                session_id text,
                state_data text,
                timestamp timestamp,
                PRIMARY KEY (user_id, session_id, timestamp)
            )
        """)
        
        # Tabla para recomendaciones generadas
        session.execute("""
            CREATE TABLE IF NOT EXISTS rl_recommendations (
                user_id text,
                session_id text,
                recommendation_id text,
                product_id text,
                confidence float,
                timestamp timestamp,
                PRIMARY KEY (user_id, session_id, recommendation_id)
            )
        """)
        
        # Tabla para recompensas del agente
        session.execute("""
            CREATE TABLE IF NOT EXISTS rl_rewards (
                user_id text,
                session_id text,
                action_id text,
                reward float,
                context text,
                timestamp timestamp,
                PRIMARY KEY (user_id, session_id, action_id)
            )
        """)
        
        # Tabla para métricas del agente
        session.execute("""
            CREATE TABLE IF NOT EXISTS rl_metrics (
                metric_name text,
                metric_value float,
                timestamp timestamp,
                PRIMARY KEY (metric_name, timestamp)
            )
        """)
        
        # Tabla para configuración del agente
        session.execute("""
            CREATE TABLE IF NOT EXISTS rl_config (
                config_key text PRIMARY KEY,
                config_value text,
                updated_at timestamp
            )
        """)
        
        # Insertar configuración inicial usando prepared statements
        insert_config = session.prepare("""
            INSERT INTO rl_config (config_key, config_value, updated_at) 
            VALUES (?, ?, ?)
        """)
        
        current_time = datetime.now()
        
        session.execute(insert_config, ('learning_rate', '0.01', current_time))
        session.execute(insert_config, ('exploration_rate', '0.1', current_time))
        session.execute(insert_config, ('discount_factor', '0.95', current_time))
        
        print("✅ Tablas de RL inicializadas correctamente")
        
        session.shutdown()
        cluster.shutdown()
        
    except Exception as e:
        print(f"❌ Error inicializando tablas RL: {e}")
        raise

if __name__ == "__main__":
    init_rl_tables() 