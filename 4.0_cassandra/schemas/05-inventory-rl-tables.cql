-- ========================================
-- REINFORCEMENT LEARNING INVENTORY TABLES
-- ========================================

USE ecommerce_analytics;

-- Tabla principal de inventario actual
CREATE TABLE IF NOT EXISTS inventory_current (
    stock_code text PRIMARY KEY,
    current_stock int,
    max_stock_capacity int,
    reorder_point int,
    safety_stock int,
    location_id text,
    storage_cost_per_unit decimal,
    last_restock_date timestamp,
    last_updated timestamp,
    updated_by text
);

-- Tabla de datos de proveedores
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id text PRIMARY KEY,
    supplier_name text,
    reliability_score double,
    average_lead_time int,
    lead_time_variance int,
    minimum_order_quantity int,
    bulk_discount_tiers map<int, double>,
    payment_terms text,
    contact_info map<text, text>,
    active boolean,
    created_at timestamp
);

-- Tabla de relación producto-proveedor
CREATE TABLE IF NOT EXISTS product_suppliers (
    stock_code text,
    supplier_id text,
    procurement_cost decimal,
    lead_time_days int,
    minimum_quantity int,
    bulk_discounts map<int, double>,
    is_primary boolean,
    contract_start_date timestamp,
    contract_end_date timestamp,
    PRIMARY KEY (stock_code, supplier_id)
);

-- Tabla de costos y configuración de productos
CREATE TABLE IF NOT EXISTS product_costs (
    stock_code text PRIMARY KEY,
    procurement_cost decimal,
    holding_cost_rate double,
    stockout_penalty decimal,
    ordering_cost decimal,
    waste_cost_rate double,
    insurance_cost_rate double,
    shelf_life_days int,
    storage_requirements text,
    abc_classification text,
    profit_margin double,
    updated_at timestamp
);

-- Tabla de métricas de demanda calculadas
CREATE TABLE IF NOT EXISTS demand_metrics (
    stock_code text,
    date_calculated date,
    daily_demand_avg double,
    demand_variance double,
    demand_trend double,
    seasonal_factor double,
    day_of_week_factors map<text, double>,
    velocity_category text,
    forecast_accuracy double,
    calculation_method text,
    PRIMARY KEY (stock_code, date_calculated)
) WITH CLUSTERING ORDER BY (date_calculated DESC);

-- Tabla de eventos de inventario (reposiciones, ajustes, etc.)
CREATE TABLE IF NOT EXISTS inventory_events (
    event_id uuid,
    stock_code text,
    event_type text, -- 'reorder', 'adjustment', 'shrinkage', 'receipt'
    event_timestamp timestamp,
    quantity_change int,
    previous_stock int,
    new_stock int,
    supplier_id text,
    cost decimal,
    reason text,
    created_by text,
    metadata map<text, text>,
    PRIMARY KEY (stock_code, event_timestamp, event_id)
) WITH CLUSTERING ORDER BY (event_timestamp DESC);

-- Tabla de simulaciones de políticas de inventario
CREATE TABLE IF NOT EXISTS inventory_simulations (
    simulation_id uuid,
    stock_code text,
    simulation_date timestamp,
    policy_type text, -- 'rl_agent', 'conservative', 'aggressive', 'manual'
    simulation_days int,
    initial_stock int,
    parameters map<text, double>,
    results map<text, double>, -- total_cost, total_revenue, stockouts, etc.
    recommendation text,
    confidence_score double,
    PRIMARY KEY (simulation_id, stock_code)
);

-- Tabla de factores estacionales y promocionales
CREATE TABLE IF NOT EXISTS seasonal_factors (
    stock_code text,
    factor_type text, -- 'seasonal', 'promotional', 'holiday'
    factor_name text,
    start_date timestamp,
    end_date timestamp,
    multiplier double,
    confidence_level double,
    historical_data boolean,
    notes text,
    PRIMARY KEY (stock_code, factor_type, factor_name)
);

-- Tabla de competencia y precios de mercado
CREATE TABLE IF NOT EXISTS market_data (
    stock_code text,
    competitor_id text,
    price_date date,
    competitor_price decimal,
    availability boolean,
    promotion_active boolean,
    market_share_estimate double,
    data_source text,
    reliability_score double,
    PRIMARY KEY (stock_code, competitor_id, price_date)
) WITH CLUSTERING ORDER BY (price_date DESC);

-- Tabla de configuración de almacenes
CREATE TABLE IF NOT EXISTS warehouse_config (
    warehouse_id text PRIMARY KEY,
    warehouse_name text,
    location text,
    total_capacity int,
    current_utilization double,
    operating_cost_per_day decimal,
    storage_cost_per_unit decimal,
    temperature_controlled boolean,
    security_level text,
    manager_contact map<text, text>,
    active boolean
);

-- Tabla de ubicaciones de productos en almacén
CREATE TABLE IF NOT EXISTS product_locations (
    stock_code text,
    warehouse_id text,
    zone text,
    aisle text,
    shelf text,
    bin text,
    current_quantity int,
    max_capacity int,
    picking_priority int,
    last_movement timestamp,
    PRIMARY KEY (stock_code, warehouse_id)
);

-- Tabla de predicciones de demanda ML/RL
CREATE TABLE IF NOT EXISTS demand_predictions (
    stock_code text,
    prediction_date date,
    prediction_horizon_days int,
    predicted_demand double,
    confidence_interval_lower double,
    confidence_interval_upper double,
    model_used text,
    model_version text,
    factors_considered list<text>,
    accuracy_score double,
    created_at timestamp,
    PRIMARY KEY (stock_code, prediction_date, prediction_horizon_days)
) WITH CLUSTERING ORDER BY (prediction_date DESC);

-- Tabla de estados del agente RL de inventarios
CREATE TABLE IF NOT EXISTS inventory_rl_states (
    agent_id text,
    stock_code text,
    state_timestamp timestamp,
    current_stock int,
    days_of_supply double,
    demand_trend double,
    demand_volatility double,
    stockout_risk double,
    action_taken text,
    order_quantity int,
    expected_cost decimal,
    expected_revenue decimal,
    confidence_score double,
    reward_received double,
    episode_id text,
    PRIMARY KEY ((agent_id, stock_code), state_timestamp)
) WITH CLUSTERING ORDER BY (state_timestamp DESC);

-- Tabla de métricas de rendimiento del agente RL
CREATE TABLE IF NOT EXISTS inventory_rl_metrics (
    agent_id text,
    metric_date date,
    total_products_managed int,
    avg_stockout_rate double,
    avg_holding_cost_ratio double,
    total_cost_savings decimal,
    service_level_achieved double,
    q_table_size int,
    exploration_rate double,
    learning_rate double,
    episodes_completed int,
    avg_reward_per_episode double,
    PRIMARY KEY (agent_id, metric_date)
) WITH CLUSTERING ORDER BY (metric_date DESC);

-- ========================================
-- INSERTAR DATOS DE EJEMPLO
-- ========================================

-- Insertar configuración de almacén ejemplo
INSERT INTO warehouse_config (
    warehouse_id, warehouse_name, location, total_capacity, 
    current_utilization, operating_cost_per_day, storage_cost_per_unit,
    temperature_controlled, security_level, active
) VALUES (
    'WH001', 'Central Warehouse', 'London, UK', 100000,
    0.75, 500.0, 0.02, true, 'high', true
);

-- Insertar proveedor ejemplo
INSERT INTO suppliers (
    supplier_id, supplier_name, reliability_score, average_lead_time,
    lead_time_variance, minimum_order_quantity, payment_terms, active, created_at
) VALUES (
    'SUP001', 'Global Supplies Ltd', 0.95, 7, 2, 100, 'NET30', true, toTimestamp(now())
);

-- Insertar factores estacionales ejemplo
INSERT INTO seasonal_factors (
    stock_code, factor_type, factor_name, start_date, end_date,
    multiplier, confidence_level, historical_data, notes
) VALUES (
    'GIFT001', 'seasonal', 'Christmas Season', '2024-12-01', '2024-12-31',
    2.5, 0.9, true, 'Historical Christmas sales spike'
);

-- Insertar costos de producto ejemplo
INSERT INTO product_costs (
    stock_code, procurement_cost, holding_cost_rate, stockout_penalty,
    ordering_cost, profit_margin, abc_classification, updated_at
) VALUES (
    'GIFT001', 10.50, 0.02, 25.0, 50.0, 0.4, 'A', toTimestamp(now())
);

-- ========================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ========================================

-- Índice para búsquedas por clasificación ABC
CREATE INDEX IF NOT EXISTS idx_product_costs_abc 
ON product_costs (abc_classification);

-- Índice para búsquedas por proveedor
CREATE INDEX IF NOT EXISTS idx_product_suppliers_supplier 
ON product_suppliers (supplier_id);

-- Índice para eventos recientes de inventario
CREATE INDEX IF NOT EXISTS idx_inventory_events_type 
ON inventory_events (event_type);

-- Índice para predicciones por modelo
CREATE INDEX IF NOT EXISTS idx_demand_predictions_model 
ON demand_predictions (model_used);

echo "✅ Tablas de RL para Inventarios creadas exitosamente"; 