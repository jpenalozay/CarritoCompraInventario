-- Datos de inventario para RL de productos principales
USE ecommerce_analytics;

-- Insertar más productos de inventario
INSERT INTO inventory_current (stock_code, current_stock, max_stock_capacity, reorder_point, safety_stock, location_id, storage_cost_per_unit, last_restock_date, last_updated, updated_by) VALUES ('85123A', 800, 1500, 300, 150, 'WH001-A-02', 0.15, '2025-01-10 10:00:00', '2025-07-17 16:20:00', 'generator');

INSERT INTO inventory_current (stock_code, current_stock, max_stock_capacity, reorder_point, safety_stock, location_id, storage_cost_per_unit, last_restock_date, last_updated, updated_by) VALUES ('71053', 650, 1200, 250, 120, 'WH001-A-03', 0.20, '2025-01-15 10:00:00', '2025-07-17 16:20:00', 'generator');

INSERT INTO inventory_current (stock_code, current_stock, max_stock_capacity, reorder_point, safety_stock, location_id, storage_cost_per_unit, last_restock_date, last_updated, updated_by) VALUES ('84029G', 450, 900, 180, 90, 'WH001-A-04', 0.18, '2025-01-20 10:00:00', '2025-07-17 16:20:00', 'generator');

INSERT INTO inventory_current (stock_code, current_stock, max_stock_capacity, reorder_point, safety_stock, location_id, storage_cost_per_unit, last_restock_date, last_updated, updated_by) VALUES ('22752', 550, 1100, 220, 110, 'WH001-A-05', 0.12, '2025-01-25 10:00:00', '2025-07-17 16:20:00', 'generator');

INSERT INTO inventory_current (stock_code, current_stock, max_stock_capacity, reorder_point, safety_stock, location_id, storage_cost_per_unit, last_restock_date, last_updated, updated_by) VALUES ('21212', 720, 1400, 280, 140, 'WH001-A-06', 0.25, '2025-02-01 10:00:00', '2025-07-17 16:20:00', 'generator');

-- Insertar costos para estos productos
INSERT INTO product_costs (stock_code, procurement_cost, holding_cost_rate, stockout_penalty, ordering_cost, waste_cost_rate, insurance_cost_rate, shelf_life_days, storage_requirements, abc_classification, profit_margin, updated_at) VALUES ('85123A', 12.75, 0.15, 4.50, 85.00, 0.04, 0.008, 1095, 'normal', 'A', 0.35, '2025-07-17 16:20:00');

INSERT INTO product_costs (stock_code, procurement_cost, holding_cost_rate, stockout_penalty, ordering_cost, waste_cost_rate, insurance_cost_rate, shelf_life_days, storage_requirements, abc_classification, profit_margin, updated_at) VALUES ('71053', 18.20, 0.12, 6.00, 120.00, 0.03, 0.012, 730, 'fragile', 'A', 0.28, '2025-07-17 16:20:00');

INSERT INTO product_costs (stock_code, procurement_cost, holding_cost_rate, stockout_penalty, ordering_cost, waste_cost_rate, insurance_cost_rate, shelf_life_days, storage_requirements, abc_classification, profit_margin, updated_at) VALUES ('84029G', 14.50, 0.18, 5.25, 95.00, 0.05, 0.010, 365, 'climate_controlled', 'B', 0.42, '2025-07-17 16:20:00');

INSERT INTO product_costs (stock_code, procurement_cost, holding_cost_rate, stockout_penalty, ordering_cost, waste_cost_rate, insurance_cost_rate, shelf_life_days, storage_requirements, abc_classification, profit_margin, updated_at) VALUES ('22752', 8.90, 0.14, 3.75, 75.00, 0.06, 0.006, 1825, 'normal', 'B', 0.38, '2025-07-17 16:20:00');

INSERT INTO product_costs (stock_code, procurement_cost, holding_cost_rate, stockout_penalty, ordering_cost, waste_cost_rate, insurance_cost_rate, shelf_life_days, storage_requirements, abc_classification, profit_margin, updated_at) VALUES ('21212', 22.40, 0.20, 8.50, 150.00, 0.02, 0.015, 545, 'climate_controlled', 'A', 0.32, '2025-07-17 16:20:00');

-- Insertar más proveedores
INSERT INTO suppliers (supplier_id, supplier_name, reliability_score, average_lead_time, lead_time_variance, minimum_order_quantity, payment_terms, active, created_at) VALUES ('SUP002', 'Fashion Forward Inc', 0.88, 12, 3, 75, 'NET45', true, '2025-07-17 16:20:00');

INSERT INTO suppliers (supplier_id, supplier_name, reliability_score, average_lead_time, lead_time_variance, minimum_order_quantity, payment_terms, active, created_at) VALUES ('SUP003', 'Electronics Pro', 0.92, 8, 2, 150, 'NET15', true, '2025-07-17 16:20:00');

INSERT INTO suppliers (supplier_id, supplier_name, reliability_score, average_lead_time, lead_time_variance, minimum_order_quantity, payment_terms, active, created_at) VALUES ('SUP004', 'Home & Garden Co', 0.85, 15, 4, 50, 'NET60', true, '2025-07-17 16:20:00');

-- Insertar relaciones producto-proveedor
INSERT INTO product_suppliers (stock_code, supplier_id, procurement_cost, lead_time_days, minimum_quantity, is_primary, contract_start_date, contract_end_date) VALUES ('22423', 'SUP001', 15.50, 10, 100, true, '2024-01-01 00:00:00', '2025-12-31 23:59:59');

INSERT INTO product_suppliers (stock_code, supplier_id, procurement_cost, lead_time_days, minimum_quantity, is_primary, contract_start_date, contract_end_date) VALUES ('85123A', 'SUP002', 12.75, 12, 75, true, '2024-01-01 00:00:00', '2025-12-31 23:59:59');

INSERT INTO product_suppliers (stock_code, supplier_id, procurement_cost, lead_time_days, minimum_quantity, is_primary, contract_start_date, contract_end_date) VALUES ('71053', 'SUP003', 18.20, 8, 150, true, '2024-01-01 00:00:00', '2025-12-31 23:59:59');

INSERT INTO product_suppliers (stock_code, supplier_id, procurement_cost, lead_time_days, minimum_quantity, is_primary, contract_start_date, contract_end_date) VALUES ('84029G', 'SUP001', 14.50, 10, 100, true, '2024-01-01 00:00:00', '2025-12-31 23:59:59');

INSERT INTO product_suppliers (stock_code, supplier_id, procurement_cost, lead_time_days, minimum_quantity, is_primary, contract_start_date, contract_end_date) VALUES ('22752', 'SUP004', 8.90, 15, 50, true, '2024-01-01 00:00:00', '2025-12-31 23:59:59');

INSERT INTO product_suppliers (stock_code, supplier_id, procurement_cost, lead_time_days, minimum_quantity, is_primary, contract_start_date, contract_end_date) VALUES ('21212', 'SUP002', 22.40, 12, 75, true, '2024-01-01 00:00:00', '2025-12-31 23:59:59');

-- Insertar métricas de demanda
INSERT INTO demand_metrics (stock_code, date_calculated, daily_demand_avg, demand_variance, demand_trend, seasonal_factor, velocity_category, forecast_accuracy, calculation_method) VALUES ('22423', '2025-07-17', 25.5, 8.2, 0.05, 1.1, 'A', 0.89, 'historical_analysis');

INSERT INTO demand_metrics (stock_code, date_calculated, daily_demand_avg, demand_variance, demand_trend, seasonal_factor, velocity_category, forecast_accuracy, calculation_method) VALUES ('85123A', '2025-07-17', 18.7, 6.4, 0.08, 1.2, 'A', 0.92, 'historical_analysis');

INSERT INTO demand_metrics (stock_code, date_calculated, daily_demand_avg, demand_variance, demand_trend, seasonal_factor, velocity_category, forecast_accuracy, calculation_method) VALUES ('71053', '2025-07-17', 22.1, 9.1, -0.02, 0.95, 'A', 0.87, 'historical_analysis');

INSERT INTO demand_metrics (stock_code, date_calculated, daily_demand_avg, demand_variance, demand_trend, seasonal_factor, velocity_category, forecast_accuracy, calculation_method) VALUES ('84029G', '2025-07-17', 15.3, 5.8, 0.12, 1.15, 'B', 0.85, 'historical_analysis');

INSERT INTO demand_metrics (stock_code, date_calculated, daily_demand_avg, demand_variance, demand_trend, seasonal_factor, velocity_category, forecast_accuracy, calculation_method) VALUES ('22752', '2025-07-17', 12.8, 4.2, 0.03, 1.05, 'B', 0.88, 'historical_analysis');

INSERT INTO demand_metrics (stock_code, date_calculated, daily_demand_avg, demand_variance, demand_trend, seasonal_factor, velocity_category, forecast_accuracy, calculation_method) VALUES ('21212', '2025-07-17', 28.9, 11.5, 0.15, 1.25, 'A', 0.91, 'historical_analysis'); 