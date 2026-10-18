-- Blog 07 — Delta Live Tables: Declarative Pipelines That Fix Themselves
-- Exercise 3: CDC on a product catalog with apply_changes
-- Requires: Time to get your hands dirty. All three exercises generate their own data — no downloads, no external services.

-- Seed bronze once
CREATE TABLE IF NOT EXISTS bronze_product_changes
USING DELTA AS
SELECT * FROM json.`/tmp/exercises/streamcart/product_changes`;

CREATE TABLE IF NOT EXISTS silver_products (product_id STRING, price DOUBLE, updated_at TIMESTAMP)
USING DELTA;

-- Latest-wins sequencing + delete-on-tombstone, idempotent on re-run
MERGE INTO silver_products AS t
USING (
  SELECT product_id, price, updated_at, op,
         ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY updated_at DESC) AS rn
  FROM bronze_product_changes
) AS s
ON t.product_id = s.product_id AND s.rn = 1
WHEN MATCHED AND s.op = 'd' THEN DELETE
WHEN MATCHED THEN UPDATE SET t.price = s.price, t.updated_at = s.updated_at
WHEN NOT MATCHED AND s.op != 'd' THEN INSERT (product_id, price, updated_at)
  VALUES (s.product_id, s.price, s.updated_at);
