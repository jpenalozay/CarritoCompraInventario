#!/usr/bin/env python3
"""
API REST para el sistema de RL de Gestión de Inventarios
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from cassandra.cluster import Cluster
from redis import Redis
import json
import logging
from datetime import datetime, timedelta
from inventory_rl_agent import InventoryRLAgent, InventoryState
import os
from dotenv import load_dotenv
import numpy as np

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

# Variables globales
cassandra_session = None
redis_client = None
inventory_agent = None

def init_connections():
    """Inicializar conexiones a Cassandra y Redis"""
    global cassandra_session, redis_client, inventory_agent
    
    try:
        # Conectar a Cassandra
        cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
        cassandra_session = cluster.connect('ecommerce_analytics')
        logger.info("✅ Conectado a Cassandra")
        
        # Conectar a Redis
        redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Conectado a Redis")
        
        # Inicializar agente RL de inventarios
        inventory_agent = InventoryRLAgent(cassandra_session, redis_client)
        logger.info("✅ Agente RL de Inventarios inicializado")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando conexiones: {e}")
        raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check del servicio"""
    try:
        # Verificar conexiones
        redis_client.ping()
        cassandra_session.execute("SELECT now() FROM system.local")
        
        return jsonify({
            "success": True,
            "status": "healthy",
            "service": "Inventory RL API",
            "timestamp": datetime.now().isoformat(),
            "connections": {
                "cassandra": "connected",
                "redis": "connected"
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/api/v1/inventory/recommendations', methods=['POST'])
def get_inventory_recommendations():
    """Obtener recomendaciones de inventario para productos específicos"""
    try:
        data = request.get_json()
        
        if 'stock_codes' not in data:
            return jsonify({
                "success": False,
                "error": "stock_codes es requerido"
            }), 400
        
        stock_codes = data['stock_codes']
        if not isinstance(stock_codes, list):
            return jsonify({
                "success": False,
                "error": "stock_codes debe ser una lista"
            }), 400
        
        # Obtener recomendaciones
        recommendations = inventory_agent.get_inventory_recommendations(stock_codes)
        
        return jsonify({
            "success": True,
            "data": recommendations,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting inventory recommendations: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v1/inventory/state/<stock_code>', methods=['GET'])
def get_inventory_state(stock_code):
    """Obtener estado actual del inventario para un producto"""
    try:
        state = inventory_agent.environment.get_inventory_state(stock_code)
        
        return jsonify({
            "success": True,
            "data": {
                "stock_code": state.stock_code,
                "current_stock": state.current_stock,
                "days_of_supply": state.days_of_supply,
                "demand_trend": state.demand_trend,
                "demand_volatility": state.demand_volatility,
                "seasonal_factor": state.seasonal_factor,
                "velocity_category": state.velocity_category,
                "stockout_risk": state.stockout_risk,
                "supplier_lead_time": state.supplier_lead_time,
                "storage_utilization": state.storage_utilization
            },
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting inventory state for {stock_code}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v1/inventory/analytics', methods=['GET'])
def get_inventory_analytics():
    """Obtener análisis general del inventario"""
    try:
        # Obtener productos más vendidos
        top_products_query = """
            SELECT stock_code, SUM(quantity) as total_quantity, COUNT(*) as transactions
            FROM transactions 
            WHERE invoice_date >= ?
            GROUP BY stock_code
            ORDER BY total_quantity DESC
            LIMIT 20
        """
        
        cutoff_date = datetime.now() - timedelta(days=30)
        results = cassandra_session.execute(top_products_query, [cutoff_date])
        
        top_products = []
        for row in results:
            top_products.append({
                "stock_code": row.stock_code,
                "total_quantity": row.total_quantity,
                "transactions": row.transactions,
                "avg_per_transaction": row.total_quantity / row.transactions
            })
        
        # Obtener recomendaciones para los top productos
        stock_codes = [p["stock_code"] for p in top_products[:10]]
        recommendations = inventory_agent.get_inventory_recommendations(stock_codes)
        
        return jsonify({
            "success": True,
            "data": {
                "top_products": top_products,
                "recommendations_summary": {
                    "total_analyzed": len(stock_codes),
                    "critical_actions": len([r for r in recommendations["recommendations"].values() 
                                           if r.get("priority") == "critical"]),
                    "high_priority": len([r for r in recommendations["recommendations"].values() 
                                        if r.get("priority") == "high"]),
                    "total_order_value": sum([r.get("expected_cost", 0) 
                                            for r in recommendations["recommendations"].values()])
                },
                "recommendations": recommendations["recommendations"]
            },
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting inventory analytics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v1/inventory/simulation', methods=['POST'])
def run_inventory_simulation():
    """Ejecutar simulación de políticas de inventario"""
    try:
        data = request.get_json()
        
        stock_code = data.get('stock_code')
        simulation_days = data.get('days', 30)
        
        if not stock_code:
            return jsonify({
                "success": False,
                "error": "stock_code es requerido"
            }), 400
        
        # Obtener estado inicial
        initial_state = inventory_agent.environment.get_inventory_state(stock_code)
        
        # Simular diferentes escenarios
        scenarios = {
            "conservative": {"epsilon": 0.01, "reorder_threshold": 0.3},
            "balanced": {"epsilon": 0.05, "reorder_threshold": 0.5},
            "aggressive": {"epsilon": 0.1, "reorder_threshold": 0.7}
        }
        
        simulation_results = {}
        
        for scenario_name, params in scenarios.items():
            # Simular política durante N días
            total_cost = 0.0
            total_revenue = 0.0
            stockouts = 0
            
            current_stock = initial_state.current_stock
            
            for day in range(simulation_days):
                # Simular demanda diaria
                daily_demand = max(0, int(np.random.normal(
                    initial_state.demand_trend, 
                    initial_state.demand_volatility * initial_state.demand_trend
                )))
                
                # Actualizar stock
                current_stock = max(0, current_stock - daily_demand)
                
                # Verificar si necesita reposición
                stockout_risk = 1 / (1 + current_stock / (daily_demand + 1))
                
                if stockout_risk > params["reorder_threshold"]:
                    order_qty = int(initial_state.demand_trend * 14)  # 2 semanas de inventario
                    current_stock += order_qty
                    total_cost += order_qty * 10.0  # Costo de procurement
                
                # Calcular revenue
                sales = min(daily_demand, current_stock)
                total_revenue += sales * 15.0
                
                # Contar stockouts
                if current_stock == 0 and daily_demand > 0:
                    stockouts += 1
                    total_cost += 50.0  # Penalización por stockout
                
                # Costo de holding
                total_cost += current_stock * initial_state.holding_cost_rate
            
            simulation_results[scenario_name] = {
                "total_cost": total_cost,
                "total_revenue": total_revenue,
                "net_profit": total_revenue - total_cost,
                "stockouts": stockouts,
                "final_stock": current_stock,
                "roi": (total_revenue - total_cost) / (total_cost + 1e-6)
            }
        
        return jsonify({
            "success": True,
            "data": {
                "stock_code": stock_code,
                "simulation_days": simulation_days,
                "initial_state": {
                    "current_stock": initial_state.current_stock,
                    "demand_trend": initial_state.demand_trend,
                    "stockout_risk": initial_state.stockout_risk
                },
                "scenarios": simulation_results,
                "recommendation": max(simulation_results.keys(), 
                                    key=lambda k: simulation_results[k]["roi"])
            },
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error running inventory simulation: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v1/inventory/metrics', methods=['GET'])
def get_inventory_metrics():
    """Obtener métricas del modelo RL de inventarios"""
    try:
        # Obtener métricas del agente
        q_table_size = len(inventory_agent.q_table)
        
        # Métricas de rendimiento (simuladas)
        metrics = {
            "model_performance": {
                "q_table_size": q_table_size,
                "epsilon": inventory_agent.epsilon,
                "learning_rate": inventory_agent.learning_rate,
                "discount_factor": inventory_agent.discount_factor
            },
            "business_metrics": {
                "avg_inventory_turnover": 8.5,  # Simulado
                "stockout_rate": 0.02,          # 2% de stockouts
                "holding_cost_ratio": 0.15,     # 15% del valor del inventario
                "service_level": 0.98           # 98% nivel de servicio
            },
            "cost_optimization": {
                "total_holding_cost": inventory_agent.total_holding_cost,
                "total_stockout_cost": inventory_agent.total_stockout_cost,
                "estimated_savings": 15000.0    # Ahorros estimados vs. política manual
            }
        }
        
        return jsonify({
            "success": True,
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting inventory metrics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/v1/inventory/update', methods=['POST'])
def update_inventory():
    """Actualizar inventario manual (para simulación)"""
    try:
        data = request.get_json()
        
        required_fields = ['stock_code', 'new_stock']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"{field} es requerido"
                }), 400
        
        stock_code = data['stock_code']
        new_stock = int(data['new_stock'])
        
        # Actualizar en Redis
        redis_key = f"inventory:current:{stock_code}"
        redis_client.hset(redis_key, mapping={
            'stock': new_stock,
            'last_updated': datetime.now().isoformat(),
            'updated_by': 'manual'
        })
        
        return jsonify({
            "success": True,
            "message": f"Inventario actualizado para {stock_code}",
            "data": {
                "stock_code": stock_code,
                "new_stock": new_stock,
                "updated_at": datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating inventory: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Inicializar conexiones
    init_connections()
    
    # Iniciar servidor
    port = int(os.getenv('INVENTORY_API_PORT', 5000))
    
    print("=" * 50)
    print("🤖 INVENTORY RL API INICIADO")
    print("=" * 50)
    print(f"📊 API URL: http://localhost:{port}")
    print(f"💚 Health Check: http://localhost:{port}/health")
    print(f"📈 Inventory Analytics: http://localhost:{port}/api/v1/inventory/analytics")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=True) 