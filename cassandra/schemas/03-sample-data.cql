-- Sample data for testing E-commerce Analytics
USE ecommerce_analytics;

-- Sample revenue data
INSERT INTO revenue_by_country_time 
(country, date_bucket, hour, timestamp, invoice_no, customer_id, revenue_gbp, revenue_usd, order_count, customer_count, avg_order_value, created_at, updated_at)
VALUES 
('United Kingdom', '2025-07-04', 10, '2025-07-04 10:30:00', 'INV001', 'CUST001', 125.50, 158.75, 1, 1, 125.50, '2025-07-04 10:30:00', '2025-07-04 10:30:00');

INSERT INTO revenue_by_country_time 
(country, date_bucket, hour, timestamp, invoice_no, customer_id, revenue_gbp, revenue_usd, order_count, customer_count, avg_order_value, created_at, updated_at)
VALUES 
('Germany', '2025-07-04', 11, '2025-07-04 11:15:00', 'INV002', 'CUST002', 89.99, 114.25, 1, 1, 89.99, '2025-07-04 11:15:00', '2025-07-04 11:15:00');

INSERT INTO revenue_by_country_time 
(country, date_bucket, hour, timestamp, invoice_no, customer_id, revenue_gbp, revenue_usd, order_count, customer_count, avg_order_value, created_at, updated_at)
VALUES 
('France', '2025-07-04', 12, '2025-07-04 12:45:00', 'INV003', 'CUST003', 67.25, 85.32, 1, 1, 67.25, '2025-07-04 12:45:00', '2025-07-04 12:45:00');

INSERT INTO revenue_by_country_time 
(country, date_bucket, hour, timestamp, invoice_no, customer_id, revenue_gbp, revenue_usd, order_count, customer_count, avg_order_value, created_at, updated_at)
VALUES 
('Netherlands', '2025-07-04', 9, '2025-07-04 09:20:00', 'INV004', 'CUST004', 156.80, 199.11, 1, 1, 156.80, '2025-07-04 09:20:00', '2025-07-04 09:20:00');

-- Sample customer analytics data
INSERT INTO customer_analytics_by_country 
(country, customer_segment, customer_id, analysis_date, recency_days, frequency_count, monetary_value, rfm_score, lifetime_value, first_purchase_date, last_purchase_date, total_orders, total_spent, avg_order_value, preferred_categories, churn_risk_score, created_at, updated_at)
VALUES 
('United Kingdom', 'VIP', 'CUST001', '2025-07-04', 5, 15, 1250.50, 'RFM_555', 2500.00, '2024-01-15', '2025-06-29', 15, 1250.50, 83.37, {'Electronics', 'Books'}, 0.15, '2025-07-04 10:00:00', '2025-07-04 10:00:00');

INSERT INTO customer_analytics_by_country 
(country, customer_segment, customer_id, analysis_date, recency_days, frequency_count, monetary_value, rfm_score, lifetime_value, first_purchase_date, last_purchase_date, total_orders, total_spent, avg_order_value, preferred_categories, churn_risk_score, created_at, updated_at)
VALUES 
('Germany', 'Regular', 'CUST002', '2025-07-04', 12, 8, 650.75, 'RFM_344', 1200.00, '2024-03-20', '2025-06-22', 8, 650.75, 81.34, {'Home', 'Garden'}, 0.35, '2025-07-04 10:00:00', '2025-07-04 10:00:00');

-- Sample real-time metrics
INSERT INTO realtime_metrics 
(metric_type, country, timestamp, metric_value, metric_unit, metadata, alert_threshold, is_anomaly, previous_value, percentage_change, trend_direction, created_at)
VALUES 
('revenue', 'United Kingdom', '2025-07-04 10:30:00', 125.50, 'GBP', {'source': 'flink', 'version': '1.0'}, 100.00, false, 110.25, 13.83, 'UP', '2025-07-04 10:30:00');

INSERT INTO realtime_metrics 
(metric_type, country, timestamp, metric_value, metric_unit, metadata, alert_threshold, is_anomaly, previous_value, percentage_change, trend_direction, created_at)
VALUES 
('orders', 'Germany', '2025-07-04 11:15:00', 15, 'count', {'source': 'flink', 'version': '1.0'}, 10, false, 12, 25.00, 'UP', '2025-07-04 11:15:00');

INSERT INTO realtime_metrics 
(metric_type, country, timestamp, metric_value, metric_unit, metadata, alert_threshold, is_anomaly, previous_value, percentage_change, trend_direction, created_at)
VALUES 
('conversion_rate', 'France', '2025-07-04 12:45:00', 3.2, 'percentage', {'source': 'flink', 'version': '1.0'}, 2.5, false, 2.9, 10.34, 'UP', '2025-07-04 12:45:00');

-- Sample product performance data
INSERT INTO product_performance_by_region 
(region, product_category, performance_date, revenue_rank, product_id, product_description, stock_code, units_sold, revenue_total, revenue_growth_rate, profit_margin, cross_sell_revenue, created_at, updated_at)
VALUES 
('Europe', 'Electronics', '2025-07-04', 1, 'PROD001', 'Wireless Headphones', 'WH001', 25, 1250.00, 15.5, 35.2, 250.00, '2025-07-04 10:00:00', '2025-07-04 10:00:00');

INSERT INTO product_performance_by_region 
(region, product_category, performance_date, revenue_rank, product_id, product_description, stock_code, units_sold, revenue_total, revenue_growth_rate, profit_margin, cross_sell_revenue, created_at, updated_at)
VALUES 
('Europe', 'Books', '2025-07-04', 2, 'PROD002', 'Data Science Handbook', 'BK002', 18, 890.00, 8.3, 45.0, 150.00, '2025-07-04 10:00:00', '2025-07-04 10:00:00');

-- Sample ML features
INSERT INTO ml_features_store 
(feature_group, entity_id, feature_timestamp, features, model_version, feature_version, computation_method, completeness_score, freshness_minutes, is_valid, created_at)
VALUES 
('customer_features', 'CUST001', '2025-07-04 10:30:00', {'recency': 5.0, 'frequency': 15.0, 'monetary': 1250.5, 'avg_order_value': 83.37, 'days_since_first': 535.0}, 'v1.2', 'v1.0', 'realtime', 1.0, 5, true, '2025-07-04 10:30:00');

INSERT INTO ml_features_store 
(feature_group, entity_id, feature_timestamp, features, model_version, feature_version, computation_method, completeness_score, freshness_minutes, is_valid, created_at)
VALUES 
('product_features', 'PROD001', '2025-07-04 10:30:00', {'avg_rating': 4.5, 'review_count': 125.0, 'price_tier': 3.0, 'category_popularity': 0.85, 'seasonal_factor': 1.2}, 'v1.2', 'v1.0', 'batch', 0.95, 30, true, '2025-07-04 10:00:00');

-- Sample customer journey events
INSERT INTO customer_journey_events 
(customer_id, session_date, event_timestamp, event_sequence, session_id, event_type, event_category, page_url, product_id, product_name, product_category, product_price, device_type, browser, country, cart_value_at_event, cart_item_count, is_conversion_event, created_at)
VALUES 
('CUST001', '2025-07-04', '2025-07-04 10:25:00', 1, 'SES001', 'page_view', 'navigation', '/products/electronics', null, null, null, null, 'desktop', 'chrome', 'United Kingdom', 0.0, 0, false, '2025-07-04 10:25:00');

INSERT INTO customer_journey_events 
(customer_id, session_date, event_timestamp, event_sequence, session_id, event_type, event_category, page_url, product_id, product_name, product_category, product_price, device_type, browser, country, cart_value_at_event, cart_item_count, is_conversion_event, created_at)
VALUES 
('CUST001', '2025-07-04', '2025-07-04 10:28:00', 2, 'SES001', 'add_to_cart', 'interaction', '/products/WH001', 'PROD001', 'Wireless Headphones', 'Electronics', 50.00, 'desktop', 'chrome', 'United Kingdom', 50.00, 1, false, '2025-07-04 10:28:00');

INSERT INTO customer_journey_events 
(customer_id, session_date, event_timestamp, event_sequence, session_id, event_type, event_category, page_url, product_id, product_name, product_category, product_price, device_type, browser, country, cart_value_at_event, cart_item_count, is_conversion_event, created_at)
VALUES 
('CUST001', '2025-07-04', '2025-07-04 10:30:00', 3, 'SES001', 'purchase', 'transaction', '/checkout/success', 'PROD001', 'Wireless Headphones', 'Electronics', 50.00, 'desktop', 'chrome', 'United Kingdom', 50.00, 1, true, '2025-07-04 10:30:00');