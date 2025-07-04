-- ========================================
-- TABLE CREATION FOR E-COMMERCE ANALYTICS
-- ========================================

-- E-commerce Analytics Tables
USE ecommerce_analytics;

-- Revenue Analytics Table
CREATE TABLE revenue_by_country_time (
    country text,
    date_bucket date,
    hour int,
    timestamp timestamp,
    invoice_no text,
    customer_id text,
    revenue_gbp decimal,
    revenue_usd decimal,
    order_count int,
    customer_count int,
    avg_order_value decimal,
    created_at timestamp,
    updated_at timestamp,
    PRIMARY KEY ((country, date_bucket), hour, timestamp)
) WITH CLUSTERING ORDER BY (hour ASC, timestamp DESC);

-- Customer Analytics Table
CREATE TABLE customer_analytics_by_country (
    country text,
    customer_segment text,
    customer_id text,
    analysis_date date,
    recency_days int,
    frequency_count int,
    monetary_value decimal,
    rfm_score text,
    lifetime_value decimal,
    first_purchase_date date,
    last_purchase_date date,
    total_orders int,
    total_spent decimal,
    avg_order_value decimal,
    preferred_categories set<text>,
    churn_risk_score decimal,
    created_at timestamp,
    updated_at timestamp,
    PRIMARY KEY ((country, customer_segment), customer_id, analysis_date)
) WITH CLUSTERING ORDER BY (customer_id ASC, analysis_date DESC);

-- Product Performance Table
CREATE TABLE product_performance_by_region (
    region text,
    product_category text,
    performance_date date,
    revenue_rank int,
    product_id text,
    product_description text,
    stock_code text,
    units_sold int,
    revenue_total decimal,
    revenue_growth_rate decimal,
    profit_margin decimal,
    cross_sell_revenue decimal,
    created_at timestamp,
    updated_at timestamp,
    PRIMARY KEY ((region, product_category), performance_date, revenue_rank, product_id)
) WITH CLUSTERING ORDER BY (performance_date DESC, revenue_rank ASC, product_id ASC);

-- Real-time Metrics Table
CREATE TABLE realtime_metrics (
    metric_type text,
    country text,
    timestamp timestamp,
    metric_value double,
    metric_unit text,
    metadata map<text, text>,
    alert_threshold double,
    is_anomaly boolean,
    previous_value double,
    percentage_change double,
    trend_direction text,
    created_at timestamp,
    PRIMARY KEY ((metric_type, country), timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC)
  AND default_time_to_live = 604800;

-- ML Features Store Table
CREATE TABLE ml_features_store (
    feature_group text,
    entity_id text,
    feature_timestamp timestamp,
    features map<text, double>,
    model_version text,
    feature_version text,
    computation_method text,
    completeness_score decimal,
    freshness_minutes int,
    is_valid boolean,
    created_at timestamp,
    PRIMARY KEY ((feature_group, entity_id), feature_timestamp)
) WITH CLUSTERING ORDER BY (feature_timestamp DESC)
  AND default_time_to_live = 2592000;

-- Customer Journey Events Table
CREATE TABLE customer_journey_events (
    customer_id text,
    session_date date,
    event_timestamp timestamp,
    event_sequence int,
    session_id text,
    event_type text,
    event_category text,
    page_url text,
    product_id text,
    product_name text,
    product_category text,
    product_price decimal,
    device_type text,
    browser text,
    country text,
    cart_value_at_event decimal,
    cart_item_count int,
    is_conversion_event boolean,
    created_at timestamp,
    PRIMARY KEY ((customer_id, session_date), event_timestamp, event_sequence)
) WITH CLUSTERING ORDER BY (event_timestamp ASC, event_sequence ASC)
  AND default_time_to_live = 7776000;