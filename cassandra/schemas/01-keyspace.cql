-- ========================================
-- KEYSPACE CREATION
-- ========================================

-- Drop keyspace if exists (for development)
DROP KEYSPACE IF EXISTS ecommerce_analytics;

-- Create main keyspace
CREATE KEYSPACE ecommerce_analytics
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1  -- Single node for development
}
AND durable_writes = true;

-- Use the keyspace
USE ecommerce_analytics;

-- Verify keyspace creation
DESCRIBE KEYSPACE ecommerce_analytics;