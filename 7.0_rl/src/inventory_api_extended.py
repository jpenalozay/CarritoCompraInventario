#!/usr/bin/env python3
"""
API extendido para Reinforcement Learning de Inventarios
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from cassandra.cluster import Cluster
from datetime import datetime, timedelta
import os
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Cassandra
CASSANDRA_HOST = os.getenv('CASSANDRA_HOST', 'cassandra')
CASSANDRA_PORT = int(os.getenv('CASSANDRA_PORT', 9042))

cluster = Cluster([CASSANDRA_HOST], port=CASSANDRA_PORT)
session = cluster.connect('ecommerce_analytics')

@app.route('/api/inventory/status', methods=['GET'])
def get_inventory_status():
    """Obtener estado actual del inventario"""
    try:
        query = """
            SELECT ic.stock_code, ic.current_stock, ic.max_stock_capacity, 
                   ic.reorder_point, ic.safety_stock, ic.location_id,
                   pc.abc_classification, pc.procurement_cost, pc.profit_margin,
                   dm.daily_demand_avg, dm.velocity_category
            FROM inventory_current ic
            LEFT JOIN product_costs pc ON ic.stock_code = pc.stock_code
            LEFT JOIN demand_metrics dm ON ic.stock_code = dm.stock_code
        """
        
        results = session.execute(query)
        inventory = []
        
        for row in results:
            # Calcular métricas
            days_supply = (row.current_stock / max(row.daily_demand_avg or 1, 1)) if row.daily_demand_avg else 0
            utilization = (row.current_stock / row.max_stock_capacity) if row.max_stock_capacity else 0
            
            # Estado del stock
            if row.current_stock <= (row.safety_stock or 0):
                status = 'CRITICAL'
            elif row.current_stock <= (row.reorder_point or 0):
                status = 'LOW'
            elif utilization > 0.8:
                status = 'HIGH'
            else:
                status = 'NORMAL'
            
            item = {
                'stock_code': row.stock_code,
                'current_stock': row.current_stock,
                'max_capacity': row.max_stock_capacity,
                'reorder_point': row.reorder_point,
                'safety_stock': row.safety_stock,
                'location': row.location_id,
                'abc_class': row.abc_classification,
                'procurement_cost': float(row.procurement_cost) if row.procurement_cost else 0,
                'profit_margin': float(row.profit_margin) if row.profit_margin else 0,
                'daily_demand': float(row.daily_demand_avg) if row.daily_demand_avg else 0,
                'days_of_supply': round(days_supply, 1),
                'utilization_pct': round(utilization * 100, 1),
                'status': status,
                'velocity': row.velocity_category or 'C'
            }
            inventory.append(item)
        
        # Estadísticas generales
        total_products = len(inventory)
        critical_count = len([i for i in inventory if i['status'] == 'CRITICAL'])
        low_count = len([i for i in inventory if i['status'] == 'LOW'])
        
        stats = {
            'total_products': total_products,
            'critical_stock': critical_count,
            'low_stock': low_count,
            'normal_stock': total_products - critical_count - low_count,
            'avg_utilization': round(sum(i['utilization_pct'] for i in inventory) / max(total_products, 1), 1)
        }
        
        return jsonify({
            'status': 'success',
            'data': inventory,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting inventory status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/inventory/recommendations', methods=['GET'])
def get_recommendations():
    """Obtener recomendaciones de RL"""
    try:
        # Parámetros de consulta
        priority = request.args.get('priority', 'ALL')
        limit = int(request.args.get('limit', 20))
        
        # Query base
        query = """
            SELECT stock_code, recommendation_date, recommended_action, order_quantity,
                   current_stock, days_of_supply, stockout_risk, priority, created_at
            FROM inventory_recommendations
            WHERE recommendation_date >= ?
        """
        
        params = [datetime.now().date() - timedelta(days=7)]  # Última semana
        
        if priority != 'ALL':
            query += " AND priority = ? ALLOW FILTERING"
            params.append(priority)
        
        query += " LIMIT ?"
        params.append(limit)
        
        results = session.execute(query, params)
        recommendations = []
        
        for row in results:
            rec = {
                'stock_code': row.stock_code,
                'date': row.recommendation_date.isoformat(),
                'action': row.recommended_action,
                'order_quantity': row.order_quantity,
                'current_stock': row.current_stock,
                'days_of_supply': round(row.days_of_supply, 1),
                'stockout_risk': round(row.stockout_risk, 3),
                'priority': row.priority,
                'created_at': row.created_at.isoformat()
            }
            recommendations.append(rec)
        
        # Estadísticas de recomendaciones
        priority_stats = {}
        action_stats = {}
        
        for rec in recommendations:
            priority_stats[rec['priority']] = priority_stats.get(rec['priority'], 0) + 1
            action_stats[rec['action']] = action_stats.get(rec['action'], 0) + 1
        
        return jsonify({
            'status': 'success',
            'data': recommendations,
            'stats': {
                'total_recommendations': len(recommendations),
                'by_priority': priority_stats,
                'by_action': action_stats
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/inventory/suppliers', methods=['GET'])
def get_suppliers():
    """Obtener información de proveedores"""
    try:
        query = """
            SELECT supplier_id, supplier_name, reliability_score, average_lead_time,
                   minimum_order_quantity, payment_terms, active
            FROM suppliers
            WHERE active = true
        """
        
        results = session.execute(query)
        suppliers = []
        
        for row in results:
            supplier = {
                'id': row.supplier_id,
                'name': row.supplier_name,
                'reliability': round(row.reliability_score, 2),
                'lead_time_avg': row.average_lead_time,
                'min_order_qty': row.minimum_order_quantity,
                'payment_terms': row.payment_terms,
                'status': 'Active' if row.active else 'Inactive'
            }
            suppliers.append(supplier)
        
        return jsonify({
            'status': 'success',
            'data': suppliers,
            'count': len(suppliers),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting suppliers: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/inventory/events', methods=['GET'])
def get_inventory_events():
    """Obtener eventos recientes de inventario"""
    try:
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 50))
        
        query = """
            SELECT stock_code, event_type, event_timestamp, quantity_change,
                   new_stock, reason, created_by
            FROM inventory_events
            WHERE event_timestamp >= ?
            LIMIT ?
            ALLOW FILTERING
        """
        
        start_date = datetime.now() - timedelta(days=days)
        results = session.execute(query, [start_date, limit])
        
        events = []
        for row in results:
            event = {
                'stock_code': row.stock_code,
                'event_type': row.event_type,
                'timestamp': row.event_timestamp.isoformat(),
                'quantity_change': row.quantity_change,
                'new_stock': row.new_stock,
                'reason': row.reason,
                'created_by': row.created_by
            }
            events.append(event)
        
        # Estadísticas de eventos
        event_types = {}
        for event in events:
            event_types[event['event_type']] = event_types.get(event['event_type'], 0) + 1
        
        return jsonify({
            'status': 'success',
            'data': events,
            'stats': {
                'total_events': len(events),
                'by_type': event_types,
                'period_days': days
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting inventory events: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/inventory/product/<stock_code>', methods=['GET'])
def get_product_details(stock_code):
    """Obtener detalles completos de un producto"""
    try:
        # Información básica de inventario
        inventory_query = """
            SELECT * FROM inventory_current WHERE stock_code = ?
        """
        inventory_result = session.execute(inventory_query, [stock_code])
        inventory_row = inventory_result.one()
        
        if not inventory_row:
            return jsonify({'status': 'error', 'message': 'Product not found'}), 404
        
        # Información de costos
        costs_query = """
            SELECT * FROM product_costs WHERE stock_code = ?
        """
        costs_result = session.execute(costs_query, [stock_code])
        costs_row = costs_result.one()
        
        # Métricas de demanda
        demand_query = """
            SELECT * FROM demand_metrics WHERE stock_code = ? LIMIT 1
        """
        demand_result = session.execute(demand_query, [stock_code])
        demand_row = demand_result.one()
        
        # Proveedor principal
        supplier_query = """
            SELECT ps.*, s.supplier_name, s.reliability_score
            FROM product_suppliers ps
            LEFT JOIN suppliers s ON ps.supplier_id = s.supplier_id
            WHERE ps.stock_code = ? AND ps.is_primary = true
        """
        supplier_result = session.execute(supplier_query, [stock_code])
        supplier_row = supplier_result.one()
        
        # Eventos recientes
        events_query = """
            SELECT event_type, event_timestamp, quantity_change, reason
            FROM inventory_events
            WHERE stock_code = ?
            LIMIT 10
            ALLOW FILTERING
        """
        events_result = session.execute(events_query, [stock_code])
        
        # Construir respuesta
        product_details = {
            'stock_code': stock_code,
            'inventory': {
                'current_stock': inventory_row.current_stock,
                'max_capacity': inventory_row.max_stock_capacity,
                'reorder_point': inventory_row.reorder_point,
                'safety_stock': inventory_row.safety_stock,
                'location': inventory_row.location_id,
                'last_restock': inventory_row.last_restock_date.isoformat() if inventory_row.last_restock_date else None,
                'last_updated': inventory_row.last_updated.isoformat() if inventory_row.last_updated else None
            },
            'costs': {
                'procurement_cost': float(costs_row.procurement_cost) if costs_row and costs_row.procurement_cost else 0,
                'holding_cost_rate': float(costs_row.holding_cost_rate) if costs_row and costs_row.holding_cost_rate else 0,
                'stockout_penalty': float(costs_row.stockout_penalty) if costs_row and costs_row.stockout_penalty else 0,
                'profit_margin': float(costs_row.profit_margin) if costs_row and costs_row.profit_margin else 0,
                'abc_classification': costs_row.abc_classification if costs_row else 'C'
            } if costs_row else {},
            'demand': {
                'daily_avg': float(demand_row.daily_demand_avg) if demand_row and demand_row.daily_demand_avg else 0,
                'variance': float(demand_row.demand_variance) if demand_row and demand_row.demand_variance else 0,
                'trend': float(demand_row.demand_trend) if demand_row and demand_row.demand_trend else 0,
                'seasonal_factor': float(demand_row.seasonal_factor) if demand_row and demand_row.seasonal_factor else 1.0,
                'velocity_category': demand_row.velocity_category if demand_row else 'C'
            } if demand_row else {},
            'supplier': {
                'id': supplier_row.supplier_id if supplier_row else None,
                'name': supplier_row.supplier_name if supplier_row else None,
                'reliability': float(supplier_row.reliability_score) if supplier_row and supplier_row.reliability_score else 0,
                'lead_time': supplier_row.lead_time_days if supplier_row else 0,
                'min_quantity': supplier_row.minimum_quantity if supplier_row else 0
            } if supplier_row else {},
            'recent_events': [
                {
                    'type': row.event_type,
                    'timestamp': row.event_timestamp.isoformat(),
                    'quantity_change': row.quantity_change,
                    'reason': row.reason
                } for row in events_result
            ]
        }
        
        return jsonify({
            'status': 'success',
            'data': product_details,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting product details: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/inventory/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """Obtener analíticas para dashboard de inventario"""
    try:
        # Métricas generales
        inventory_query = """
            SELECT COUNT(*) as total_products FROM inventory_current
        """
        inventory_result = session.execute(inventory_query)
        total_products = inventory_result.one().total_products
        
        # Distribución por clasificación ABC
        abc_query = """
            SELECT abc_classification, COUNT(*) as count 
            FROM product_costs 
            GROUP BY abc_classification 
            ALLOW FILTERING
        """
        abc_result = session.execute(abc_query)
        abc_distribution = {row.abc_classification: row.count for row in abc_result}
        
        # Proveedores activos
        suppliers_query = """
            SELECT COUNT(*) as active_suppliers FROM suppliers WHERE active = true ALLOW FILTERING
        """
        suppliers_result = session.execute(suppliers_query)
        active_suppliers = suppliers_result.one().active_suppliers
        
        # Eventos recientes (últimos 7 días)
        events_query = """
            SELECT COUNT(*) as recent_events FROM inventory_events 
            WHERE event_timestamp >= ? ALLOW FILTERING
        """
        week_ago = datetime.now() - timedelta(days=7)
        events_result = session.execute(events_query, [week_ago])
        recent_events = events_result.one().recent_events
        
        # Recomendaciones pendientes
        recommendations_query = """
            SELECT COUNT(*) as pending_recommendations FROM inventory_recommendations 
            WHERE recommendation_date = ? ALLOW FILTERING
        """
        recommendations_result = session.execute(recommendations_query, [datetime.now().date()])
        pending_recommendations = recommendations_result.one().pending_recommendations
        
        dashboard_data = {
            'overview': {
                'total_products': total_products,
                'active_suppliers': active_suppliers,
                'recent_events': recent_events,
                'pending_recommendations': pending_recommendations
            },
            'abc_distribution': abc_distribution,
            'alerts': {
                'critical_stock': 0,  # Se calcularía con lógica adicional
                'overstock': 0,
                'supplier_issues': 0
            },
            'performance': {
                'inventory_turnover': 0,  # Se calcularía con datos históricos
                'stockout_rate': 0,
                'fill_rate': 0
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': dashboard_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test connection to Cassandra
        session.execute("SELECT now() FROM system.local")
        return jsonify({
            'status': 'healthy',
            'service': 'inventory-rl-api',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'inventory-rl-api',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Inventory RL API...")
    app.run(host='0.0.0.0', port=5002, debug=False) 