#!/usr/bin/env python3
"""
Agente de Reinforcement Learning para Gestión Inteligente de Inventarios
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import json
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class InventoryAction(Enum):
    """Acciones posibles para gestión de inventario"""
    NO_REORDER = "no_reorder"
    REORDER_LOW = "reorder_low"        # 25% del stock máximo
    REORDER_MEDIUM = "reorder_medium"  # 50% del stock máximo
    REORDER_HIGH = "reorder_high"      # 75% del stock máximo
    LIQUIDATION = "liquidation"        # Descuento para liquidar
    EMERGENCY_ORDER = "emergency"      # Orden urgente (costo extra)

@dataclass
class InventoryState:
    """Estado del inventario para un producto específico"""
    stock_code: str
    current_stock: int
    days_of_supply: float           # Días de inventario restante
    demand_trend: float             # Tendencia de demanda (7 días)
    demand_volatility: float        # Volatilidad de la demanda
    seasonal_factor: float          # Factor estacional
    velocity_category: str          # A, B, C (clasificación ABC)
    holding_cost_rate: float        # Costo de mantener inventario
    stockout_risk: float           # Probabilidad de desabasto
    profit_margin: float           # Margen de ganancia del producto
    supplier_lead_time: int        # Tiempo de entrega del proveedor
    storage_utilization: float     # % de capacidad de almacén usado

@dataclass
class InventoryActionResult:
    """Resultado de una acción de inventario"""
    action: InventoryAction
    order_quantity: int
    expected_cost: float
    expected_revenue: float
    confidence_score: float
    metadata: Dict

class InventoryEnvironment:
    """Entorno de simulación para gestión de inventarios"""
    
    def __init__(self, cassandra_session, redis_client):
        self.cassandra_session = cassandra_session
        self.redis_client = redis_client
        self.action_space = list(InventoryAction)
        
    def get_inventory_state(self, stock_code: str) -> InventoryState:
        """Obtener estado actual del inventario para un producto"""
        try:
            # 1. Obtener datos de transacciones recientes (últimos 30 días)
            recent_sales = self._get_recent_sales(stock_code, days=30)
            
            # 2. Calcular métricas de demanda
            demand_metrics = self._calculate_demand_metrics(recent_sales)
            
            # 3. Obtener datos de inventario actual (simulado con datos básicos)
            inventory_data = self._get_current_inventory(stock_code)
            
            # 4. Calcular estado
            return InventoryState(
                stock_code=stock_code,
                current_stock=inventory_data.get('current_stock', 0),
                days_of_supply=self._calculate_days_of_supply(
                    inventory_data.get('current_stock', 0),
                    demand_metrics['daily_avg']
                ),
                demand_trend=demand_metrics['trend'],
                demand_volatility=demand_metrics['volatility'],
                seasonal_factor=self._get_seasonal_factor(stock_code),
                velocity_category=self._classify_velocity(demand_metrics['daily_avg']),
                holding_cost_rate=0.02,  # 2% mensual (simulado)
                stockout_risk=self._calculate_stockout_risk(
                    inventory_data.get('current_stock', 0),
                    demand_metrics['daily_avg'],
                    demand_metrics['volatility']
                ),
                profit_margin=self._estimate_profit_margin(stock_code),
                supplier_lead_time=7,  # 7 días (simulado)
                storage_utilization=0.75  # 75% (simulado)
            )
            
        except Exception as e:
            logger.error(f"Error getting inventory state for {stock_code}: {e}")
            return self._get_default_state(stock_code)
    
    def _get_recent_sales(self, stock_code: str, days: int = 30) -> List[Dict]:
        """Obtener ventas recientes de un producto"""
        try:
            # Consultar Cassandra por ventas recientes
            query = """
                SELECT invoice_date, quantity, unit_price, country
                FROM transactions 
                WHERE stock_code = ? 
                AND invoice_date >= ?
            """
            
            cutoff_date = datetime.now() - timedelta(days=days)
            results = self.cassandra_session.execute(query, [stock_code, cutoff_date])
            
            sales_data = []
            for row in results:
                sales_data.append({
                    'date': row.invoice_date,
                    'quantity': row.quantity,
                    'unit_price': row.unit_price,
                    'country': row.country,
                    'revenue': row.quantity * row.unit_price
                })
            
            return sales_data
            
        except Exception as e:
            logger.error(f"Error getting recent sales for {stock_code}: {e}")
            return []
    
    def _calculate_demand_metrics(self, sales_data: List[Dict]) -> Dict:
        """Calcular métricas de demanda basadas en ventas históricas"""
        if not sales_data:
            return {
                'daily_avg': 0.0,
                'trend': 0.0,
                'volatility': 0.0
            }
        
        # Agrupar ventas por día
        daily_sales = {}
        for sale in sales_data:
            date_key = sale['date'].strftime('%Y-%m-%d')
            if date_key not in daily_sales:
                daily_sales[date_key] = 0
            daily_sales[date_key] += sale['quantity']
        
        quantities = list(daily_sales.values())
        
        # Calcular métricas
        daily_avg = np.mean(quantities) if quantities else 0.0
        volatility = np.std(quantities) / (daily_avg + 1e-6)  # Coeficiente de variación
        
        # Calcular tendencia (últimos 7 días vs 7 días anteriores)
        if len(quantities) >= 14:
            recent_avg = np.mean(quantities[-7:])
            previous_avg = np.mean(quantities[-14:-7])
            trend = (recent_avg - previous_avg) / (previous_avg + 1e-6)
        else:
            trend = 0.0
        
        return {
            'daily_avg': daily_avg,
            'trend': trend,
            'volatility': volatility
        }
    
    def _calculate_days_of_supply(self, current_stock: int, daily_demand: float) -> float:
        """Calcular días de inventario restante"""
        if daily_demand <= 0:
            return float('inf')
        return current_stock / daily_demand
    
    def _classify_velocity(self, daily_demand: float) -> str:
        """Clasificar productos por velocidad de venta (ABC)"""
        if daily_demand >= 10:
            return "A"  # Alta rotación
        elif daily_demand >= 3:
            return "B"  # Media rotación
        else:
            return "C"  # Baja rotación
    
    def _calculate_stockout_risk(self, current_stock: int, daily_demand: float, volatility: float) -> float:
        """Calcular probabilidad de desabastecimiento"""
        if daily_demand <= 0:
            return 0.0
        
        # Simulación simple: riesgo basado en días de inventario y volatilidad
        days_supply = current_stock / (daily_demand + 1e-6)
        
        # Mayor volatilidad = mayor riesgo
        risk_factor = 1 + volatility
        
        # Función sigmoidea para normalizar riesgo
        stockout_risk = 1 / (1 + np.exp((days_supply - 5) / risk_factor))
        
        return min(max(stockout_risk, 0.0), 1.0)
    
    def _get_seasonal_factor(self, stock_code: str) -> float:
        """Obtener factor estacional (simulado)"""
        # En implementación real, esto vendría de análisis histórico
        month = datetime.now().month
        
        # Simulación simple: productos tienen picos en diferentes meses
        seasonal_patterns = {
            'winter': [12, 1, 2],
            'spring': [3, 4, 5],
            'summer': [6, 7, 8],
            'autumn': [9, 10, 11]
        }
        
        # Hash del stock_code para asignar patrón consistente
        pattern_hash = hash(stock_code) % 4
        patterns = list(seasonal_patterns.values())
        
        if month in patterns[pattern_hash]:
            return 1.3  # 30% más demanda en temporada alta
        else:
            return 1.0  # Demanda normal
    
    def _estimate_profit_margin(self, stock_code: str) -> float:
        """Estimar margen de ganancia (simulado)"""
        # En implementación real, esto vendría de datos de costos
        return 0.25  # 25% de margen promedio
    
    def _get_current_inventory(self, stock_code: str) -> Dict:
        """Obtener inventario actual (simulado)"""
        # NOTA: En implementación real, esto vendría de sistema de inventarios
        # Por ahora simulamos basado en ventas recientes
        
        try:
            # Intentar obtener de Redis si existe
            redis_key = f"inventory:current:{stock_code}"
            inventory_data = self.redis_client.hgetall(redis_key)
            
            if inventory_data:
                return {
                    'current_stock': int(inventory_data.get('stock', 0)),
                    'max_capacity': int(inventory_data.get('max_capacity', 1000)),
                    'reorder_point': int(inventory_data.get('reorder_point', 50))
                }
            else:
                # Simular inventario inicial
                simulated_stock = np.random.randint(10, 200)
                return {
                    'current_stock': simulated_stock,
                    'max_capacity': 1000,
                    'reorder_point': 50
                }
                
        except Exception as e:
            logger.error(f"Error getting current inventory for {stock_code}: {e}")
            return {'current_stock': 0, 'max_capacity': 1000, 'reorder_point': 50}
    
    def _get_default_state(self, stock_code: str) -> InventoryState:
        """Estado por defecto en caso de error"""
        return InventoryState(
            stock_code=stock_code,
            current_stock=0,
            days_of_supply=0.0,
            demand_trend=0.0,
            demand_volatility=1.0,
            seasonal_factor=1.0,
            velocity_category="C",
            holding_cost_rate=0.02,
            stockout_risk=0.5,
            profit_margin=0.25,
            supplier_lead_time=7,
            storage_utilization=0.75
        )

class InventoryRLAgent:
    """Agente RL para optimización de inventarios"""
    
    def __init__(self, cassandra_session, redis_client, model_version="v1.0"):
        self.cassandra_session = cassandra_session
        self.redis_client = redis_client
        self.model_version = model_version
        self.environment = InventoryEnvironment(cassandra_session, redis_client)
        
        # Parámetros específicos para inventarios
        self.epsilon = 0.05  # Menor exploración (decisiones más conservadoras)
        self.learning_rate = 0.001  # Aprendizaje más lento
        self.discount_factor = 0.99  # Mayor consideración del futuro
        
        # Q-table para estados de inventario
        self.q_table = {}
        
        # Métricas específicas de inventario
        self.total_holding_cost = 0.0
        self.total_stockout_cost = 0.0
        self.total_revenue = 0.0
        
    def select_inventory_action(self, state: InventoryState) -> InventoryActionResult:
        """Seleccionar acción de inventario óptima"""
        state_key = self._state_to_key(state)
        
        # Política epsilon-greedy específica para inventarios
        if np.random.random() < self.epsilon:
            # Exploración: acción aleatoria ponderada por riesgo
            action = self._safe_random_action(state)
        else:
            # Explotación: mejor acción conocida
            if state_key in self.q_table:
                action = max(self.q_table[state_key], key=self.q_table[state_key].get)
            else:
                action = self._policy_based_action(state)
        
        # Calcular cantidad a ordenar y métricas
        order_quantity = self._calculate_order_quantity(state, action)
        expected_cost = self._estimate_cost(state, action, order_quantity)
        expected_revenue = self._estimate_revenue(state, action, order_quantity)
        confidence = self._calculate_confidence(state, action)
        
        return InventoryActionResult(
            action=action,
            order_quantity=order_quantity,
            expected_cost=expected_cost,
            expected_revenue=expected_revenue,
            confidence_score=confidence,
            metadata={
                "model_version": self.model_version,
                "state_key": state_key,
                "risk_level": self._assess_risk_level(state)
            }
        )
    
    def _state_to_key(self, state: InventoryState) -> str:
        """Convertir estado a clave discreta para Q-table"""
        # Discretizar variables continuas
        stock_level = "low" if state.current_stock < 50 else "medium" if state.current_stock < 200 else "high"
        demand_level = "low" if state.demand_trend < -0.1 else "medium" if state.demand_trend < 0.1 else "high"
        risk_level = "low" if state.stockout_risk < 0.3 else "medium" if state.stockout_risk < 0.7 else "high"
        
        return f"{state.velocity_category}_{stock_level}_{demand_level}_{risk_level}_{state.seasonal_factor:.1f}"
    
    def _safe_random_action(self, state: InventoryState) -> InventoryAction:
        """Acción aleatoria ponderada por riesgo"""
        # Si el riesgo de desabasto es alto, priorizar reposición
        if state.stockout_risk > 0.7:
            return np.random.choice([
                InventoryAction.REORDER_MEDIUM,
                InventoryAction.REORDER_HIGH,
                InventoryAction.EMERGENCY_ORDER
            ])
        # Si el inventario es alto, considerar no reordenar o liquidar
        elif state.current_stock > 150:
            return np.random.choice([
                InventoryAction.NO_REORDER,
                InventoryAction.LIQUIDATION
            ])
        else:
            return np.random.choice(self.environment.action_space)
    
    def _policy_based_action(self, state: InventoryState) -> InventoryAction:
        """Acción basada en reglas de negocio (política por defecto)"""
        # Reglas de inventario clásicas mejoradas
        
        # Emergencia: stock muy bajo y alta demanda
        if state.days_of_supply < 2 and state.demand_trend > 0:
            return InventoryAction.EMERGENCY_ORDER
        
        # Liquidación: exceso de inventario y baja demanda
        if state.days_of_supply > 30 and state.demand_trend < -0.2:
            return InventoryAction.LIQUIDATION
        
        # Reposición normal basada en punto de reorden
        if state.stockout_risk > 0.5:
            if state.velocity_category == "A":
                return InventoryAction.REORDER_HIGH
            elif state.velocity_category == "B":
                return InventoryAction.REORDER_MEDIUM
            else:
                return InventoryAction.REORDER_LOW
        
        return InventoryAction.NO_REORDER
    
    def _calculate_order_quantity(self, state: InventoryState, action: InventoryAction) -> int:
        """Calcular cantidad óptima a ordenar"""
        if action == InventoryAction.NO_REORDER:
            return 0
        
        # Calcular demanda esperada durante lead time
        lead_time_demand = state.demand_trend * state.supplier_lead_time * state.seasonal_factor
        safety_stock = lead_time_demand * state.demand_volatility * 1.65  # 95% nivel de servicio
        
        # Cantidad base según tipo de acción
        quantity_multipliers = {
            InventoryAction.REORDER_LOW: 0.25,
            InventoryAction.REORDER_MEDIUM: 0.5,
            InventoryAction.REORDER_HIGH: 0.75,
            InventoryAction.EMERGENCY_ORDER: 1.0,
            InventoryAction.LIQUIDATION: 0.0
        }
        
        max_capacity = 1000  # Simulado
        target_stock = max_capacity * quantity_multipliers.get(action, 0.5)
        order_quantity = max(0, int(target_stock - state.current_stock + safety_stock))
        
        return min(order_quantity, max_capacity - state.current_stock)
    
    def _estimate_cost(self, state: InventoryState, action: InventoryAction, quantity: int) -> float:
        """Estimar costo de la acción"""
        if quantity == 0:
            return 0.0
        
        # Costos base
        procurement_cost = quantity * 10.0  # $10 por unidad (simulado)
        holding_cost = quantity * state.holding_cost_rate * 30  # Costo mensual
        
        # Costos especiales
        if action == InventoryAction.EMERGENCY_ORDER:
            procurement_cost *= 1.5  # 50% más caro
        elif action == InventoryAction.LIQUIDATION:
            return quantity * 2.0  # Costo de descuento
        
        return procurement_cost + holding_cost
    
    def _estimate_revenue(self, state: InventoryState, action: InventoryAction, quantity: int) -> float:
        """Estimar revenue potencial"""
        if action == InventoryAction.LIQUIDATION:
            return state.current_stock * 8.0  # Precio reducido
        
        # Revenue esperado basado en demanda futura
        expected_sales = min(quantity + state.current_stock, 
                           state.demand_trend * 30 * state.seasonal_factor)
        
        return expected_sales * 15.0 * state.profit_margin  # $15 precio de venta
    
    def _calculate_confidence(self, state: InventoryState, action: InventoryAction) -> float:
        """Calcular confianza en la decisión"""
        confidence = 0.5  # Base
        
        # Mayor confianza con datos más estables
        if state.demand_volatility < 0.5:
            confidence += 0.3
        
        # Mayor confianza en productos de alta rotación
        if state.velocity_category == "A":
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _assess_risk_level(self, state: InventoryState) -> str:
        """Evaluar nivel de riesgo general"""
        risk_score = (
            state.stockout_risk * 0.4 +
            state.demand_volatility * 0.3 +
            (1 - state.profit_margin) * 0.3
        )
        
        if risk_score > 0.7:
            return "high"
        elif risk_score > 0.4:
            return "medium"
        else:
            return "low"
    
    def calculate_inventory_reward(self, state: InventoryState, action: InventoryActionResult, 
                                 next_state: InventoryState) -> float:
        """Calcular recompensa específica para inventarios"""
        reward = 0.0
        
        # Recompensa por ventas realizadas
        sales_increase = max(0, next_state.current_stock - state.current_stock + action.order_quantity)
        reward += sales_increase * 2.0  # $2 por unidad vendida
        
        # Penalización por costos de inventario
        holding_cost = next_state.current_stock * state.holding_cost_rate
        reward -= holding_cost
        
        # Penalización severa por desabastecimiento
        if next_state.stockout_risk > 0.8:
            reward -= 100.0  # Penalización fija por riesgo alto
        
        # Recompensa por rotación optimizada
        if 5 <= next_state.days_of_supply <= 15:  # Rango óptimo
            reward += 20.0
        
        # Penalización por exceso de inventario
        if next_state.days_of_supply > 30:
            reward -= (next_state.days_of_supply - 30) * 2.0
        
        return reward
    
    def get_inventory_recommendations(self, stock_codes: List[str]) -> Dict:
        """Obtener recomendaciones de inventario para múltiples productos"""
        recommendations = {}
        
        for stock_code in stock_codes:
            try:
                state = self.environment.get_inventory_state(stock_code)
                action_result = self.select_inventory_action(state)
                
                recommendations[stock_code] = {
                    "action": action_result.action.value,
                    "order_quantity": action_result.order_quantity,
                    "current_stock": state.current_stock,
                    "days_of_supply": state.days_of_supply,
                    "stockout_risk": state.stockout_risk,
                    "expected_cost": action_result.expected_cost,
                    "expected_revenue": action_result.expected_revenue,
                    "confidence": action_result.confidence_score,
                    "priority": self._calculate_priority(state),
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error processing {stock_code}: {e}")
                recommendations[stock_code] = {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        return {
            "recommendations": recommendations,
            "total_products": len(stock_codes),
            "successful": len([r for r in recommendations.values() if "error" not in r]),
            "model_version": self.model_version,
            "generated_at": datetime.now().isoformat()
        }
    
    def _calculate_priority(self, state: InventoryState) -> str:
        """Calcular prioridad de acción"""
        priority_score = (
            state.stockout_risk * 0.5 +
            (1 / (state.days_of_supply + 1)) * 0.3 +
            {"A": 0.2, "B": 0.1, "C": 0.05}[state.velocity_category]
        )
        
        if priority_score > 0.7:
            return "critical"
        elif priority_score > 0.4:
            return "high"
        elif priority_score > 0.2:
            return "medium"
        else:
            return "low" 