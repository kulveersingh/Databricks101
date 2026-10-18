-- Blog 09 — Change Data Capture: Streaming Your Database to the Lakehouse
-- Exercise 3: Schema drift into a rescued column
-- Requires: All three exercises generate their own change streams — no Debezium, no Kafka, no database required.

CREATE TABLE IF NOT EXISTS silver_orders_drifted (
  order_id STRING, order_status STRING, updated_at TIMESTAMP, _rescued_data STRING
) USING DELTA;

MERGE INTO silver_orders_drifted AS t
USING (
  SELECT order_id, order_status, updated_at, _rescued_data, op,
         ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) AS rn
  FROM bronze_rescued
) AS s
ON t.order_id = s.order_id AND s.rn = 1
WHEN MATCHED AND s.op = 'd' THEN DELETE
WHEN MATCHED THEN UPDATE SET t.order_status = s.order_status, t.updated_at = s.updated_at,
                              t._rescued_data = s._rescued_data
WHEN NOT MATCHED AND s.op != 'd' THEN INSERT
  VALUES (s.order_id, s.order_status, s.updated_at, s._rescued_data);

-- The alert signal: rescued rows per batch
SELECT CASE WHEN _rescued_data LIKE '%loyalty_tier%' THEN 'drifted' ELSE 'clean' END AS batch,
       COUNT(*) AS rows
FROM silver_orders_drifted
GROUP BY 1;
