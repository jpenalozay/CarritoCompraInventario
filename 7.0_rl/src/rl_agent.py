#!/usr/bin/env python3
"""
Reinforcement Learning Agent for E-commerce Product Recommendations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import json
import uuid
from datetime import datetime, timedelta
from cassandra.cluster import Cluster
from redis import Redis
import logging
from dataclasses import dataclass
from enum import Enum
import random

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionType(Enum):
    RECOMMEND_LOW_PRICE = "low_price"
    RECOMMEND_MEDIUM_PRICE = "medium_price"
    RECOMMEND_HIGH_PRICE = "high_price"
    RECOMMEND_CATEGORY_MATCH = "category_match"
    RECOMMEND_POPULAR = "popular"
    RECOMMEND_PERSONALIZED = "personalized"

@dataclass
class State:
    """Estado del entorno de RL"""
    customer_id: str
    session_id: str
    cart_total: float
    cart_item_count: int
    time_in_session: int
    category_preferences: Dict[str, float]
    price_sensitivity: float
    engagement_level: float
    country: str
    device_type: str
    hour_of_day: int
    day_of_week: int

@dataclass
class Action:
    """Acción del agente RL"""
    action_type: ActionType
    recommended_products: List[str]
    confidence_score: float
    metadata: Dict[str, any]

class EcommerceEnvironment:
    """Entorno de simulación para el agente RL"""
    
    def __init__(self, cassandra_session, redis_client):
        self.cassandra_session = cassandra_session
        self.redis_client = redis_client
        self.action_space = list(ActionType)
        self.state_dimension = 12  # Número de features del estado
        
    def get_state(self, customer_id: str, session_id: str) -> State:
        """Extraer el estado actual del cliente"""
        try:
            # Obtener datos del carrito
            cart_query = """
                SELECT cart_total, item_count, time_in_cart, category_distribution
                FROM shopping_cart_state 
                WHERE customer_id = ? AND session_id = ?
                ORDER BY cart_timestamp DESC LIMIT 1
            """
            cart_result = self.cassandra_session.execute(cart_query, [customer_id, session_id])
            
            cart_total = 0.0
            cart_item_count = 0
            time_in_cart = 0
            category_distribution = {}
            
            if cart_result.rows:
                row = cart_result.rows[0]
                cart_total = float(row.cart_total) if row.cart_total else 0.0
                cart_item_count = row.item_count if row.item_count else 0
                time_in_cart = row.time_in_cart if row.time_in_cart else 0
                category_distribution = row.category_distribution if row.category_distribution else {}
            
            # Obtener preferencias del cliente
            customer_query = """
                SELECT total_spent, total_purchases, avg_order_value, preferred_categories
                FROM customer_metrics 
                WHERE customer_id = ?
            """
            customer_result = self.cassandra_session.execute(customer_query, [customer_id])
            
            total_spent = 0.0
            total_purchases = 0
            avg_order_value = 0.0
            preferred_categories = {}
            
            if customer_result.rows:
                row = customer_result.rows[0]
                total_spent = float(row.total_spent) if row.total_spent else 0.0
                total_purchases = row.total_purchases if row.total_purchases else 0
                avg_order_value = float(row.avg_order_value) if row.avg_order_value else 0.0
            
            # Calcular features derivadas
            price_sensitivity = self._calculate_price_sensitivity(total_spent, total_purchases, avg_order_value)
            engagement_level = self._calculate_engagement_level(total_purchases, time_in_cart)
            
            # Obtener hora y día
            now = datetime.now()
            hour_of_day = now.hour
            day_of_week = now.weekday()
            
            return State(
                customer_id=customer_id,
                session_id=session_id,
                cart_total=cart_total,
                cart_item_count=cart_item_count,
                time_in_session=time_in_cart,
                category_preferences=category_distribution,
                price_sensitivity=price_sensitivity,
                engagement_level=engagement_level,
                country="UK",  # Por defecto, se puede extraer de los datos
                device_type="desktop",  # Por defecto
                hour_of_day=hour_of_day,
                day_of_week=day_of_week
            )
            
        except Exception as e:
            logger.error(f"Error getting state: {e}")
            # Estado por defecto
            return State(
                customer_id=customer_id,
                session_id=session_id,
                cart_total=0.0,
                cart_item_count=0,
                time_in_session=0,
                category_preferences={},
                price_sensitivity=0.5,
                engagement_level=0.5,
                country="UK",
                device_type="desktop",
                hour_of_day=datetime.now().hour,
                day_of_week=datetime.now().weekday()
            )
    
    def _calculate_price_sensitivity(self, total_spent: float, total_purchases: int, avg_order_value: float) -> float:
        """Calcular sensibilidad al precio del cliente"""
        if total_purchases == 0:
            return 0.5
        
        # Clientes con órdenes de alto valor son menos sensibles al precio
        if avg_order_value > 100:
            return 0.2
        elif avg_order_value > 50:
            return 0.5
        else:
            return 0.8
    
    def _calculate_engagement_level(self, total_purchases: int, time_in_cart: int) -> float:
        """Calcular nivel de engagement del cliente"""
        # Basado en historial de compras y tiempo en carrito
        purchase_score = min(total_purchases / 10.0, 1.0)  # Normalizar a 0-1
        time_score = min(time_in_cart / 60.0, 1.0)  # Normalizar a 0-1
        return (purchase_score + time_score) / 2.0

class RLAgent:
    """Agente de Reinforcement Learning para recomendaciones"""
    
    def __init__(self, cassandra_session, redis_client, model_version="v1.0"):
        self.cassandra_session = cassandra_session
        self.redis_client = redis_client
        self.model_version = model_version
        self.environment = EcommerceEnvironment(cassandra_session, redis_client)
        
        # Parámetros del agente
        self.epsilon = 0.1  # Tasa de exploración
        self.learning_rate = 0.01
        self.discount_factor = 0.95
        
        # Q-table (simplificado para demostración)
        self.q_table = {}
        
        # Historial de episodios
        self.current_episode = str(uuid.uuid4())
        
    def select_action(self, state: State) -> Action:
        """Seleccionar acción usando política epsilon-greedy"""
        state_key = self._state_to_key(state)
        
        # Exploración vs explotación
        if np.random.random() < self.epsilon:
            # Exploración: acción aleatoria
            action_type = np.random.choice(self.environment.action_space)
        else:
            # Explotación: mejor acción conocida
            if state_key in self.q_table:
                action_type = max(self.q_table[state_key], key=self.q_table[state_key].get)
            else:
                action_type = np.random.choice(self.environment.action_space)
        
        # Generar recomendaciones basadas en la acción
        recommended_products = self._generate_recommendations(state, action_type)
        confidence_score = self._calculate_confidence(state, action_type)
        
        return Action(
            action_type=action_type,
            recommended_products=recommended_products,
            confidence_score=confidence_score,
            metadata={"episode_id": self.current_episode}
        )
    
    def _state_to_key(self, state: State) -> str:
        """Convertir estado a clave para Q-table"""
        return f"{state.customer_id}_{state.cart_total:.0f}_{state.cart_item_count}_{state.price_sensitivity:.1f}"
    
    def _generate_recommendations(self, state: State, action_type: ActionType) -> List[str]:
        """Generar recomendaciones basadas en la acción seleccionada"""
        try:
            if action_type == ActionType.RECOMMEND_LOW_PRICE:
                # Productos de bajo precio
                query = """
                    SELECT stock_code FROM transactions 
                    WHERE unit_price < 10 
                    GROUP BY stock_code 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 5
                """
            elif action_type == ActionType.RECOMMEND_MEDIUM_PRICE:
                # Productos de precio medio
                query = """
                    SELECT stock_code FROM transactions 
                    WHERE unit_price BETWEEN 10 AND 50 
                    GROUP BY stock_code 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 5
                """
            elif action_type == ActionType.RECOMMEND_HIGH_PRICE:
                # Productos de alto precio
                query = """
                    SELECT stock_code FROM transactions 
                    WHERE unit_price > 50 
                    GROUP BY stock_code 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 5
                """
            elif action_type == ActionType.RECOMMEND_POPULAR:
                # Productos populares
                query = """
                    SELECT stock_code FROM transactions 
                    GROUP BY stock_code 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 5
                """
            else:
                # Recomendación personalizada basada en categorías preferidas
                preferred_categories = list(state.category_preferences.keys())[:3]
                if preferred_categories:
                    placeholders = ','.join(['?'] * len(preferred_categories))
                    query = f"""
                        SELECT stock_code FROM transactions 
                        WHERE description LIKE ANY(?) 
                        GROUP BY stock_code 
                        ORDER BY COUNT(*) DESC 
                        LIMIT 5
                    """
                else:
                    query = """
                        SELECT stock_code FROM transactions 
                        GROUP BY stock_code 
                        ORDER BY COUNT(*) DESC 
                        LIMIT 5
                    """
            
            result = self.cassandra_session.execute(query)
            return [row.stock_code for row in result.rows]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["DEFAULT_PRODUCT_1", "DEFAULT_PRODUCT_2", "DEFAULT_PRODUCT_3"]
    
    def _calculate_confidence(self, state: State, action_type: ActionType) -> float:
        """Calcular score de confianza para la acción"""
        # Basado en la consistencia del estado y la acción
        base_confidence = 0.5
        
        # Ajustar basado en engagement
        if state.engagement_level > 0.7:
            base_confidence += 0.2
        elif state.engagement_level < 0.3:
            base_confidence -= 0.2
        
        # Ajustar basado en sensibilidad al precio
        if action_type == ActionType.RECOMMEND_LOW_PRICE and state.price_sensitivity > 0.7:
            base_confidence += 0.3
        elif action_type == ActionType.RECOMMEND_HIGH_PRICE and state.price_sensitivity < 0.3:
            base_confidence += 0.3
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def receive_reward(self, state: State, action: Action, reward: float, next_state: State):
        """Recibir recompensa y actualizar el modelo"""
        try:
            # Actualizar Q-table
            state_key = self._state_to_key(state)
            action_key = action.action_type.value
            
            if state_key not in self.q_table:
                self.q_table[state_key] = {}
            
            if action_key not in self.q_table[state_key]:
                self.q_table[state_key][action_key] = 0.0
            
            # Q-learning update
            next_state_key = self._state_to_key(next_state)
            max_next_q = 0.0
            if next_state_key in self.q_table:
                max_next_q = max(self.q_table[next_state_key].values()) if self.q_table[next_state_key] else 0.0
            
            current_q = self.q_table[state_key][action_key]
            new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
            self.q_table[state_key][action_key] = new_q
            
            # Guardar en Cassandra
            self._save_agent_state(state, action, reward, next_state)
            
        except Exception as e:
            logger.error(f"Error receiving reward: {e}")
    
    def _save_agent_state(self, state: State, action: Action, reward: float, next_state: State):
        """Guardar estado del agente en Cassandra"""
        try:
            insert_query = """
                INSERT INTO rl_agent_state (
                    agent_id, model_version, state_timestamp, current_state, 
                    action_taken, reward_received, next_state, episode_id, 
                    is_terminal, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            current_state_dict = {
                "cart_total": state.cart_total,
                "cart_item_count": state.cart_item_count,
                "price_sensitivity": state.price_sensitivity,
                "engagement_level": state.engagement_level
            }
            
            next_state_dict = {
                "cart_total": next_state.cart_total,
                "cart_item_count": next_state.cart_item_count,
                "price_sensitivity": next_state.price_sensitivity,
                "engagement_level": next_state.engagement_level
            }
            
            metadata = {
                "session_id": state.session_id,
                "confidence_score": action.confidence_score,
                "recommended_products_count": len(action.recommended_products)
            }
            
            self.cassandra_session.execute(
                insert_query,
                [
                    "recommendation_agent",
                    self.model_version,
                    datetime.now(),
                    current_state_dict,
                    action.action_type.value,
                    reward,
                    next_state_dict,
                    self.current_episode,
                    False,
                    metadata,
                    datetime.now()
                ]
            )
            
        except Exception as e:
            logger.error(f"Error saving agent state: {e}")
    
    def get_recommendations(self, customer_id: str, session_id: str) -> Dict:
        """Obtener recomendaciones para un cliente"""
        try:
            # Obtener estado actual
            state = self.environment.get_state(customer_id, session_id)
            
            # Seleccionar acción
            action = self.select_action(state)
            
            # Guardar recomendación
            self._save_recommendation(customer_id, session_id, action)
            
            return {
                "customer_id": customer_id,
                "session_id": session_id,
                "recommendations": action.recommended_products,
                "confidence_score": action.confidence_score,
                "action_type": action.action_type.value,
                "metadata": action.metadata,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return {
                "customer_id": customer_id,
                "session_id": session_id,
                "recommendations": ["DEFAULT_PRODUCT_1", "DEFAULT_PRODUCT_2"],
                "confidence_score": 0.5,
                "action_type": "fallback",
                "metadata": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def _save_recommendation(self, customer_id: str, session_id: str, action: Action):
        """Guardar recomendación en Cassandra"""
        try:
            insert_query = """
                INSERT INTO rl_recommendations (
                    customer_id, session_id, recommendation_timestamp,
                    recommended_products, recommendation_scores, context_features,
                    action_type, conversion_result, revenue_generated,
                    model_version, confidence_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Generar scores aleatorios para demostración
            scores = [action.confidence_score * np.random.uniform(0.8, 1.2) for _ in action.recommended_products]
            
            context_features = {
                "cart_total": 0.0,  # Se puede extraer del estado
                "engagement_level": 0.5,
                "price_sensitivity": 0.5
            }
            
            self.cassandra_session.execute(
                insert_query,
                [
                    customer_id,
                    session_id,
                    datetime.now(),
                    action.recommended_products,
                    scores,
                    context_features,
                    action.action_type.value,
                    False,  # Por defecto
                    0.0,    # Revenue generado
                    self.model_version,
                    action.confidence_score,
                    datetime.now()
                ]
            )
            
        except Exception as e:
            logger.error(f"Error saving recommendation: {e}")

if __name__ == "__main__":
    # Ejemplo de uso
    print("RL Agent initialized successfully!") 