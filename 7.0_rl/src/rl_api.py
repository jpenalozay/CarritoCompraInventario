#!/usr/bin/env python3
"""
API REST para el componente de Reinforcement Learning
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from cassandra.cluster import Cluster
from redis import Redis
import json
import logging
from datetime import datetime, timedelta
from rl_agent import RLAgent, State, Action
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuración de conexiones
CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'cassandra')
CASSANDRA_PORT = int(os.getenv('CASSANDRA_PORT', '9042'))
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

# Inicializar conexiones
cassandra_session = None
redis_client = None
rl_agent = None

def init_connections():
    """Inicializar conexiones a Cassandra y Redis"""
    global cassandra_session, redis_client, rl_agent
    
    try:
        # Conectar a Cassandra
        cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
        cassandra_session = cluster.connect('ecommerce_analytics')
        logger.info("✅ Conectado a Cassandra (ecommerce_analytics)")
        
        # Conectar a Redis
        redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Conectado a Redis")
        
        # Inicializar agente RL
        rl_agent = RLAgent(cassandra_session, redis_client)
        logger.info("✅ Agente RL inicializado")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando conexiones: {e}")
        raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check del servicio RL"""
    try:
        # Verificar conexiones
        cassandra_ok = cassandra_session is not None
        redis_ok = redis_client is not None and redis_client.ping()
        agent_ok = rl_agent is not None
        
        return jsonify({
            "status": "healthy" if all([cassandra_ok, redis_ok, agent_ok]) else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "cassandra": cassandra_ok,
                "redis": redis_ok,
                "rl_agent": agent_ok
            }
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/v1/rl/recommendations', methods=['POST'])
def get_recommendations():
    """Obtener recomendaciones para un cliente"""
    try:
        data = request.get_json()
        
        if not data or 'customer_id' not in data:
            return jsonify({
                "success": False,
                "error": "customer_id es requerido"
            }), 400
        
        customer_id = data['customer_id']
        session_id = data.get('session_id', f"session_{customer_id}_{datetime.now().timestamp()}")
        
        # Obtener recomendaciones del agente RL
        recommendations = rl_agent.get_recommendations(customer_id, session_id)
        
        return jsonify({
            "success": True,
            "data": recommendations,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v1/rl/reward', methods=['POST'])
def submit_reward():
    """Enviar recompensa para entrenar el agente"""
    try:
        data = request.get_json()
        
        required_fields = ['customer_id', 'session_id', 'reward_value', 'action_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"{field} es requerido"
                }), 400
        
        customer_id = data['customer_id']
        session_id = data['session_id']
        reward_value = float(data['reward_value'])
        action_type = data['action_type']
        
        # Obtener estados actual y siguiente
        current_state = rl_agent.environment.get_state(customer_id, session_id)
        
        # Crear acción
        action = Action(
            action_type=action_type,
            recommended_products=data.get('recommended_products', []),
            confidence_score=data.get('confidence_score', 0.5),
            metadata=data.get('metadata', {})
        )
        
        # Estado siguiente (simulado para demostración)
        next_state = current_state
        
        # Enviar recompensa al agente
        rl_agent.receive_reward(current_state, action, reward_value, next_state)
        
        return jsonify({
            "success": True,
            "message": "Recompensa procesada exitosamente",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error submitting reward: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v1/rl/metrics', methods=['GET'])
def get_metrics():
    """Obtener métricas del modelo RL"""
    try:
        # Parámetros de consulta
        days = int(request.args.get('days', 7))
        # Calcular fecha de inicio
        start_date = datetime.now() - timedelta(days=days)
        # Consultar métricas de Cassandra
        query = """
            SELECT metric_name, metric_value, timestamp
            FROM rl_metrics 
            WHERE timestamp >= %s ALLOW FILTERING
        """
        result = cassandra_session.execute(query, [start_date])
        # Agrupar métricas por nombre y ordenar por timestamp en Python
        metrics = {}
        for row in result:
            if row.metric_name not in metrics:
                metrics[row.metric_name] = []
            metrics[row.metric_name].append({
                "value": row.metric_value,
                "timestamp": row.timestamp.isoformat()
            })
        # Ordenar cada lista de métricas por timestamp descendente
        for metric_list in metrics.values():
            metric_list.sort(key=lambda x: x["timestamp"], reverse=True)
        return jsonify({
            "success": True,
            "data": {
                "period_days": days,
                "metrics": metrics
            },
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v1/rl/recommendations/history', methods=['GET'])
def get_recommendations_history():
    """Obtener historial de recomendaciones"""
    try:
        customer_id = request.args.get('customer_id')
        session_id = request.args.get('session_id')
        limit = int(request.args.get('limit', 10))
        
        if not customer_id:
            return jsonify({
                "success": False,
                "error": "customer_id es requerido"
            }), 400
        
        # Construir query
        query = """
            SELECT recommendation_timestamp, recommended_products, 
                   recommendation_scores, action_type, conversion_result,
                   revenue_generated, confidence_score
            FROM rl_recommendations 
            WHERE customer_id = ?
        """
        params = [customer_id]
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        query += " ORDER BY recommendation_timestamp DESC LIMIT ?"
        params.append(limit)
        
        result = cassandra_session.execute(query, params)
        
        recommendations = []
        for row in result.rows:
            recommendations.append({
                "timestamp": row.recommendation_timestamp.isoformat(),
                "products": row.recommended_products,
                "scores": row.recommendation_scores,
                "action_type": row.action_type,
                "conversion": row.conversion_result,
                "revenue": float(row.revenue_generated) if row.revenue_generated else 0.0,
                "confidence": row.confidence_score
            })
        
        return jsonify({
            "success": True,
            "data": {
                "customer_id": customer_id,
                "session_id": session_id,
                "recommendations": recommendations,
                "total_count": len(recommendations)
            },
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting recommendations history: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v1/rl/agent/state', methods=['GET'])
def get_agent_state():
    """Obtener estado actual del agente RL"""
    try:
        # DATOS MOCK TEMPORALES - Para testing del dashboard
        logger.info("🔄 Endpoint /agent/state solicitado - usando datos mock")
        
        return jsonify({
            "success": True,
            "data": {
                "q_table_size": 125,
                "current_episode": 1,
                "epsilon": 0.1,
                "learning_rate": 0.01,
                "discount_factor": 0.99,
                "recent_actions": [
                    {"action": "reorder_medium", "reward": 0.65, "timestamp": "2025-07-22T20:30:00Z"},
                    {"action": "reorder_high", "reward": 0.78, "timestamp": "2025-07-22T20:25:00Z"},
                    {"action": "no_reorder", "reward": 0.45, "timestamp": "2025-07-22T20:20:00Z"},
                    {"action": "reorder_low", "reward": 0.55, "timestamp": "2025-07-22T20:15:00Z"},
                    {"action": "emergency_order", "reward": 0.35, "timestamp": "2025-07-22T20:10:00Z"}
                ]
            },
            "timestamp": datetime.now().isoformat(),
            "note": "Using mock data for dashboard testing"
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting agent state: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Inicializar conexiones
    init_connections()
    
    # Iniciar servidor
    port = int(os.getenv('RL_API_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 