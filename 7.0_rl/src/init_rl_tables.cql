-- ========================================
-- INITIALIZE REINFORCEMENT LEARNING TABLES
-- ========================================

USE ecommerce_analytics;

-- Tabla para almacenar el estado del agente RL
CREATE TABLE IF NOT EXISTS rl_agent_state (
    agent_id text,
    model_version text,
    state_timestamp timestamp,
    current_state map<text, double>,
    action_taken text,
    reward_received double,
    next_state map<text, double>,
    episode_id text,
    is_terminal boolean,
    metadata map<text, text>,
    created_at timestamp,
    PRIMARY KEY ((agent_id, model_version), state_timestamp)
) WITH CLUSTERING ORDER BY (state_timestamp DESC)
  AND default_time_to_live = 2592000;  -- 30 días

-- Tabla para almacenar recomendaciones generadas por RL
CREATE TABLE IF NOT EXISTS rl_recommendations (
    customer_id text,
    session_id text,
    recommendation_timestamp timestamp,
    recommended_products list<text>,
    recommendation_scores list<double>,
    context_features map<text, double>,
    action_type text, -- 'product_view', 'add_to_cart', 'purchase'
    conversion_result boolean,
    revenue_generated decimal,
    model_version text,
    confidence_score double,
    created_at timestamp,
    PRIMARY KEY ((customer_id, session_id), recommendation_timestamp)
) WITH CLUSTERING ORDER BY (recommendation_timestamp DESC)
  AND default_time_to_live = 604800;  -- 7 días

-- Tabla para almacenar el historial de recompensas
CREATE TABLE IF NOT EXISTS rl_rewards_history (
    agent_id text,
    episode_id text,
    step_number int,
    reward_timestamp timestamp,
    reward_value double,
    reward_type text, -- 'conversion', 'revenue', 'engagement', 'retention'
    context map<text, text>,
    action_taken text,
    state_features map<text, double>,
    created_at timestamp,
    PRIMARY KEY ((agent_id, episode_id), step_number, reward_timestamp)
) WITH CLUSTERING ORDER BY (step_number DESC, reward_timestamp DESC)
  AND default_time_to_live = 7776000;  -- 90 días

-- Tabla para almacenar métricas de rendimiento del modelo RL
CREATE TABLE IF NOT EXISTS rl_model_metrics (
    model_version text,
    metric_date date,
    metric_hour int,
    metric_timestamp timestamp,
    metric_name text,
    metric_value double,
    metric_unit text,
    metadata map<text, text>,
    created_at timestamp,
    PRIMARY KEY ((model_version, metric_date), metric_hour, metric_name, metric_timestamp)
) WITH CLUSTERING ORDER BY (metric_hour DESC, metric_name ASC, metric_timestamp DESC)
  AND default_time_to_live = 2592000;  -- 30 días

-- Tabla para almacenar el estado del carrito de compras
CREATE TABLE IF NOT EXISTS shopping_cart_state (
    customer_id text,
    session_id text,
    cart_timestamp timestamp,
    cart_items list<text>,
    cart_total decimal,
    item_count int,
    category_distribution map<text, int>,
    price_range text, -- 'low', 'medium', 'high'
    time_in_cart int, -- minutos
    last_activity timestamp,
    is_abandoned boolean,
    created_at timestamp,
    PRIMARY KEY ((customer_id, session_id), cart_timestamp)
) WITH CLUSTERING ORDER BY (cart_timestamp DESC)
  AND default_time_to_live = 604800;  -- 7 días

-- Tabla para almacenar eventos de interacción del usuario
CREATE TABLE IF NOT EXISTS user_interaction_events (
    customer_id text,
    session_id text,
    event_timestamp timestamp,
    event_type text, -- 'view_product', 'add_to_cart', 'remove_from_cart', 'purchase', 'abandon'
    product_id text,
    product_category text,
    product_price decimal,
    interaction_duration int, -- segundos
    page_location text,
    device_type text,
    country text,
    context_features map<text, double>,
    created_at timestamp,
    PRIMARY KEY ((customer_id, session_id), event_timestamp, event_type)
) WITH CLUSTERING ORDER BY (event_timestamp DESC, event_type ASC)
  AND default_time_to_live = 604800;  -- 7 días

-- Tabla para almacenar políticas del agente RL
CREATE TABLE IF NOT EXISTS rl_policy_store (
    model_version text,
    policy_id text,
    policy_timestamp timestamp,
    policy_type text, -- 'epsilon_greedy', 'softmax', 'ucb'
    policy_parameters map<text, double>,
    action_space list<text>,
    state_space_dimension int,
    training_episodes int,
    average_reward double,
    exploration_rate double,
    is_active boolean,
    created_at timestamp,
    PRIMARY KEY ((model_version), policy_id, policy_timestamp)
) WITH CLUSTERING ORDER BY (policy_id ASC, policy_timestamp DESC)
  AND default_time_to_live = 2592000;  -- 30 días

-- Insertar datos de ejemplo para pruebas
INSERT INTO rl_model_metrics (model_version, metric_date, metric_hour, metric_timestamp, metric_name, metric_value, metric_unit, metadata, created_at)
VALUES ('v1.0', '2025-01-20', 10, '2025-01-20 10:30:00', 'conversion_rate', 0.15, 'percentage', {'source': 'rl_agent'}, '2025-01-20 10:30:00');

INSERT INTO rl_model_metrics (model_version, metric_date, metric_hour, metric_timestamp, metric_name, metric_value, metric_unit, metadata, created_at)
VALUES ('v1.0', '2025-01-20', 10, '2025-01-20 10:30:00', 'avg_reward', 0.65, 'score', {'source': 'rl_agent'}, '2025-01-20 10:30:00');

INSERT INTO rl_model_metrics (model_version, metric_date, metric_hour, metric_timestamp, metric_name, metric_value, metric_unit, metadata, created_at)
VALUES ('v1.0', '2025-01-20', 10, '2025-01-20 10:30:00', 'confidence_score', 0.78, 'score', {'source': 'rl_agent'}, '2025-01-20 10:30:00');

-- Insertar política inicial
INSERT INTO rl_policy_store (model_version, policy_id, policy_timestamp, policy_type, policy_parameters, action_space, state_space_dimension, training_episodes, average_reward, exploration_rate, is_active, created_at)
VALUES ('v1.0', 'epsilon_greedy_v1', '2025-01-20 10:00:00', 'epsilon_greedy', {'epsilon': 0.1, 'learning_rate': 0.01}, ['low_price', 'medium_price', 'high_price', 'popular', 'personalized'], 12, 0, 0.0, 0.1, true, '2025-01-20 10:00:00');

echo "✅ Tablas de Reinforcement Learning inicializadas correctamente"; 