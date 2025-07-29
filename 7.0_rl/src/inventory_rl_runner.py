#!/usr/bin/env python3
"""
Runner para el agente RL de inventarios - usa datos reales de Cassandra
"""
import os
import sys
import time
import logging
from datetime import datetime, timedelta
from cassandra.cluster import Cluster
import json

# Importar el agente RL
from inventory_rl_agent import InventoryQLearningAgent, InventoryState

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InventoryRLRunner:
    def __init__(self):
        self.cassandra_host = os.getenv('CASSANDRA_HOST', 'cassandra')
        self.cassandra_port = int(os.getenv('CASSANDRA_PORT', 9042))
        
        # Conectar a Cassandra
        self.cluster = Cluster([self.cassandra_host], port=self.cassandra_port)
        self.session = self.cluster.connect('ecommerce_analytics')
        
        # Inicializar agente RL
        self.agent = InventoryQLearningAgent(
            learning_rate=0.1,
            discount_factor=0.95,
            epsilon=0.3,
            epsilon_decay=0.995
        )
        
    def get_products_for_rl(self):
        """Obtener productos desde Cassandra para RL"""
        query = """
            SELECT ic.stock_code, ic.current_stock, ic.max_stock_capacity, 
                   ic.reorder_point, ic.safety_stock,
                   pc.procurement_cost, pc.holding_cost_rate, pc.abc_classification,
                   pc.profit_margin, dm.daily_demand_avg, dm.demand_variance,
                   dm.seasonal_factor, ps.lead_time_days
            FROM inventory_current ic
            LEFT JOIN product_costs pc ON ic.stock_code = pc.stock_code
            LEFT JOIN demand_metrics dm ON ic.stock_code = dm.stock_code
            LEFT JOIN product_suppliers ps ON ic.stock_code = ps.stock_code
            WHERE ps.is_primary = true
            ALLOW FILTERING
        """
        
        results = self.session.execute(query)
        products = []
        
        for row in results:
            product = {
                'stock_code': row.stock_code,
                'current_stock': row.current_stock or 0,
                'max_capacity': row.max_stock_capacity or 1000,
                'reorder_point': row.reorder_point or 100,
                'safety_stock': row.safety_stock or 50,
                'procurement_cost': float(row.procurement_cost or 10.0),
                'holding_cost_rate': float(row.holding_cost_rate or 0.15),
                'abc_classification': row.abc_classification or 'C',
                'profit_margin': float(row.profit_margin or 0.30),
                'daily_demand_avg': float(row.daily_demand_avg or 5.0),
                'demand_variance': float(row.demand_variance or 2.0),
                'seasonal_factor': float(row.seasonal_factor or 1.0),
                'lead_time_days': row.lead_time_days or 10
            }
            products.append(product)
            
        logger.info(f"📦 Cargados {len(products)} productos para RL")
        return products
    
    def create_inventory_state(self, product):
        """Crear estado de inventario desde datos del producto"""
        
        # Calcular métricas derivadas
        days_of_supply = product['current_stock'] / max(product['daily_demand_avg'], 1)
        storage_utilization = product['current_stock'] / product['max_capacity']
        
        # Calcular riesgo de desabasto
        demand_with_variance = product['daily_demand_avg'] * (1 + product['demand_variance'] / 10)
        stockout_risk = max(0, min(1, (demand_with_variance * product['lead_time_days'] - product['current_stock']) / product['max_capacity']))
        
        # Tendencia de demanda simulada
        demand_trend = (product['seasonal_factor'] - 1.0) * 0.5  # Entre -0.5 y 0.5
        
        return InventoryState(
            stock_code=product['stock_code'],
            current_stock=product['current_stock'],
            days_of_supply=days_of_supply,
            demand_trend=demand_trend,
            demand_volatility=product['demand_variance'] / 10.0,
            seasonal_factor=product['seasonal_factor'],
            velocity_category=product['abc_classification'],
            holding_cost_rate=product['holding_cost_rate'],
            stockout_risk=stockout_risk,
            profit_margin=product['profit_margin'],
            supplier_lead_time=product['lead_time_days'],
            storage_utilization=storage_utilization
        )
    
    def simulate_demand(self, product, days=1):
        """Simular demanda futura basada en datos históricos"""
        import random
        
        base_demand = product['daily_demand_avg'] * days
        seasonal_adjusted = base_demand * product['seasonal_factor']
        
        # Añadir variabilidad
        variance = product['demand_variance']
        actual_demand = max(0, int(seasonal_adjusted + random.gauss(0, variance)))
        
        return actual_demand
    
    def update_inventory_in_db(self, stock_code, new_stock, action_taken, order_quantity=0):
        """Actualizar inventario en la base de datos"""
        
        # Actualizar stock actual
        update_query = """
            UPDATE inventory_current 
            SET current_stock = ?, last_updated = ?
            WHERE stock_code = ?
        """
        self.session.execute(update_query, [new_stock, datetime.now(), stock_code])
        
        # Registrar evento si hubo una acción
        if action_taken != 'do_nothing':
            event_query = """
                INSERT INTO inventory_events (
                    event_id, stock_code, event_type, event_timestamp,
                    quantity_change, new_stock, reason, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            import uuid
            quantity_change = order_quantity if action_taken.startswith('order') else 0
            
            self.session.execute(event_query, [
                uuid.uuid4(),
                stock_code,
                'rl_action',
                datetime.now(),
                quantity_change,
                new_stock,
                f"RL Agent action: {action_taken}",
                'rl_agent'
            ])
    
    def calculate_reward(self, old_state, action, new_state, product):
        """Calcular recompensa basada en el estado del inventario"""
        
        reward = 0.0
        
        # Penalización por desabasto
        if new_state.current_stock <= 0:
            reward -= 100.0  # Penalización alta por desabasto
            
        # Penalización por exceso de inventario
        if new_state.storage_utilization > 0.9:
            reward -= 20.0 * (new_state.storage_utilization - 0.9)
            
        # Recompensa por mantener stock óptimo
        if 0.3 <= new_state.storage_utilization <= 0.7:
            reward += 10.0
            
        # Costo de mantener inventario
        holding_cost = new_state.current_stock * product['procurement_cost'] * new_state.holding_cost_rate / 365
        reward -= holding_cost
        
        # Costo de pedido si se hizo un pedido
        if action.startswith('order'):
            reward -= 50.0  # Costo fijo de pedido
            
        # Bonificación por días de suministro adecuados
        if 15 <= new_state.days_of_supply <= 45:
            reward += 5.0
            
        return reward
    
    def run_simulation(self, episodes=100, days_per_episode=30):
        """Ejecutar simulación de RL"""
        logger.info(f"🎯 Iniciando simulación RL: {episodes} episodios, {days_per_episode} días cada uno")
        
        products = self.get_products_for_rl()
        if not products:
            logger.error("❌ No se encontraron productos para RL")
            return
            
        episode_rewards = []
        
        for episode in range(episodes):
            logger.info(f"📊 Episodio {episode + 1}/{episodes}")
            
            episode_reward = 0.0
            
            for day in range(days_per_episode):
                daily_rewards = []
                
                for product in products:
                    # Crear estado actual
                    current_state = self.create_inventory_state(product)
                    
                    # Agente decide acción
                    action = self.agent.choose_action(current_state)
                    
                    # Simular demanda
                    demand = self.simulate_demand(product)
                    
                    # Aplicar acción y demanda
                    new_stock = product['current_stock']
                    order_quantity = 0
                    
                    if action == 'order_small':
                        order_quantity = int(product['daily_demand_avg'] * 7)  # 1 semana
                        new_stock += order_quantity
                    elif action == 'order_medium':
                        order_quantity = int(product['daily_demand_avg'] * 14)  # 2 semanas
                        new_stock += order_quantity
                    elif action == 'order_large':
                        order_quantity = int(product['daily_demand_avg'] * 30)  # 1 mes
                        new_stock += order_quantity
                    
                    # Aplicar demanda
                    new_stock = max(0, new_stock - demand)
                    new_stock = min(new_stock, product['max_capacity'])
                    
                    # Actualizar producto
                    product['current_stock'] = new_stock
                    
                    # Crear nuevo estado
                    new_state = self.create_inventory_state(product)
                    
                    # Calcular recompensa
                    reward = self.calculate_reward(current_state, action, new_state, product)
                    daily_rewards.append(reward)
                    
                    # Entrenar agente
                    self.agent.learn(current_state, action, reward, new_state)
                    
                    # Actualizar BD cada 7 días
                    if day % 7 == 0:
                        self.update_inventory_in_db(
                            product['stock_code'], 
                            new_stock, 
                            action, 
                            order_quantity
                        )
                
                episode_reward += sum(daily_rewards)
                
                if day % 7 == 0:
                    avg_reward = sum(daily_rewards) / len(daily_rewards)
                    logger.info(f"   Día {day + 1}: Recompensa promedio = {avg_reward:.2f}")
            
            episode_rewards.append(episode_reward)
            
            # Reducir exploración
            self.agent.decay_epsilon()
            
            if (episode + 1) % 10 == 0:
                avg_episode_reward = sum(episode_rewards[-10:]) / 10
                logger.info(f"🏆 Episodios {episode - 8}-{episode + 1}: Recompensa promedio = {avg_episode_reward:.2f}")
                logger.info(f"🔍 Epsilon actual: {self.agent.epsilon:.3f}")
        
        logger.info("✅ Simulación completada!")
        return episode_rewards
    
    def generate_recommendations(self):
        """Generar recomendaciones basadas en el agente entrenado"""
        logger.info("💡 Generando recomendaciones de inventario...")
        
        products = self.get_products_for_rl()
        recommendations = []
        
        for product in products:
            current_state = self.create_inventory_state(product)
            
            # Usar política greedy (sin exploración)
            old_epsilon = self.agent.epsilon
            self.agent.epsilon = 0.0
            
            action = self.agent.choose_action(current_state)
            
            # Restaurar epsilon
            self.agent.epsilon = old_epsilon
            
            # Calcular cantidad sugerida
            if action == 'order_small':
                order_qty = int(product['daily_demand_avg'] * 7)
            elif action == 'order_medium':
                order_qty = int(product['daily_demand_avg'] * 14)
            elif action == 'order_large':
                order_qty = int(product['daily_demand_avg'] * 30)
            else:
                order_qty = 0
            
            recommendation = {
                'stock_code': product['stock_code'],
                'current_stock': product['current_stock'],
                'recommended_action': action,
                'order_quantity': order_qty,
                'days_of_supply': current_state.days_of_supply,
                'stockout_risk': current_state.stockout_risk,
                'storage_utilization': current_state.storage_utilization,
                'abc_class': product['abc_classification'],
                'priority': 'HIGH' if current_state.stockout_risk > 0.7 else 'MEDIUM' if current_state.stockout_risk > 0.3 else 'LOW'
            }
            
            recommendations.append(recommendation)
        
        # Ordenar por prioridad y riesgo
        recommendations.sort(key=lambda x: (x['priority'] == 'LOW', x['stockout_risk']), reverse=True)
        
        logger.info(f"📋 Generadas {len(recommendations)} recomendaciones")
        
        return recommendations
    
    def save_recommendations_to_db(self, recommendations):
        """Guardar recomendaciones en Cassandra"""
        logger.info("💾 Guardando recomendaciones en BD...")
        
        # Crear tabla de recomendaciones si no existe
        create_table_query = """
            CREATE TABLE IF NOT EXISTS inventory_recommendations (
                stock_code text,
                recommendation_date date,
                recommended_action text,
                order_quantity int,
                current_stock int,
                days_of_supply double,
                stockout_risk double,
                priority text,
                created_at timestamp,
                PRIMARY KEY (stock_code, recommendation_date)
            )
        """
        self.session.execute(create_table_query)
        
        # Insertar recomendaciones
        insert_query = """
            INSERT INTO inventory_recommendations (
                stock_code, recommendation_date, recommended_action, order_quantity,
                current_stock, days_of_supply, stockout_risk, priority, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        today = datetime.now().date()
        
        for rec in recommendations:
            self.session.execute(insert_query, [
                rec['stock_code'],
                today,
                rec['recommended_action'],
                rec['order_quantity'],
                rec['current_stock'],
                rec['days_of_supply'],
                rec['stockout_risk'],
                rec['priority'],
                datetime.now()
            ])
        
        logger.info(f"✅ Guardadas {len(recommendations)} recomendaciones")
    
    def run(self):
        """Ejecutar el sistema completo de RL"""
        try:
            logger.info("🚀 Iniciando sistema RL de inventarios...")
            
            # 1. Ejecutar simulación de entrenamiento
            episode_rewards = self.run_simulation(episodes=50, days_per_episode=30)
            
            # 2. Generar recomendaciones
            recommendations = self.generate_recommendations()
            
            # 3. Mostrar recomendaciones
            logger.info("\n🎯 RECOMENDACIONES DE INVENTARIO:")
            for i, rec in enumerate(recommendations[:10], 1):  # Top 10
                logger.info(f"{i:2d}. {rec['stock_code']} ({rec['abc_class']}) - {rec['priority']}")
                logger.info(f"    Stock: {rec['current_stock']} | Acción: {rec['recommended_action']}")
                logger.info(f"    Cantidad: {rec['order_quantity']} | Riesgo: {rec['stockout_risk']:.2f}")
                logger.info(f"    Días suministro: {rec['days_of_supply']:.1f} | Utilización: {rec['storage_utilization']:.1%}")
            
            # 4. Guardar en BD
            self.save_recommendations_to_db(recommendations)
            
            logger.info("✅ Sistema RL de inventarios completado exitosamente!")
            
        except Exception as e:
            logger.error(f"❌ Error en sistema RL: {e}")
            raise
        finally:
            if hasattr(self, 'cluster'):
                self.cluster.shutdown()

if __name__ == "__main__":
    runner = InventoryRLRunner()
    runner.run() 