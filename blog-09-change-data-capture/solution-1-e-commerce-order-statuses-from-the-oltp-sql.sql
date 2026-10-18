-- Blog 09 — Change Data Capture: Streaming Your Database to the Lakehouse
-- Exercise 1: E-commerce order statuses from the OLTP
-- Requires: All three exercises generate their own change streams — no Debezium, no Kafka, no database required.

CREATE TABLE IF NOT EXISTS silver_orders (
  order_id STRING, order_status STRING, updated_at TIMESTAMP
) USING DELTA;

MERGE INTO silver_orders AS t
USING (
  SELECT order_id, order_status, updated_at, op,
         ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) AS rn
  FROM bronze_order_changes
) AS s
ON t.order_id = s.order_id AND s.rn = 1
WHEN MATCHED AND s.op = 'd' THEN DELETE
WHEN MATCHED THEN UPDATE SET t.order_status = s.order_status, t.updated_at = s.updated_at
WHEN NOT MATCHED AND s.op != 'd' THEN INSERT (order_id, order_status, updated_at)
  VALUES (s.order_id, s.order_status, s.updated_at);
-- --- next cell ---

SELECT COUNT(*) AS silver_rows FROM silver_orders;
-- Run the MERGE again, then re-run the count: identical.
-- Cancelled orders check: should return 0 rows with a live status of 'cancelled'
SELECT * FROM silver_orders WHERE order_id IN (
  SELECT order_id FROM bronze_order_changes WHERE op = 'd'
);
