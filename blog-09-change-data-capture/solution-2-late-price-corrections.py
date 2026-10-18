# Blog 09 — Change Data Capture: Streaming Your Database to the Lakehouse
# Exercise 2: Late price corrections
# Requires: All three exercises generate their own change streams — no Debezium, no Kafka, no database required.

base = "/tmp/exercises/retailer/price_changes"
dbutils.fs.rm(base, True)
spark.sql("DROP TABLE IF EXISTS bronze_price_changes")
spark.sql("DROP TABLE IF EXISTS silver_products")

from datetime import datetime, timedelta
t0 = datetime.now().replace(microsecond=0)

def ts(hours):
    return (t0 - timedelta(hours=hours)).isoformat()

events = [
    {"op": "c", "product_id": "SKU-1", "price": 29.99, "updated_at": ts(50)},
    # correction arrives late, with an EARLIER timestamp than the next event...
    {"op": "u", "product_id": "SKU-1", "price": 34.99, "updated_at": ts(20)},
    {"op": "u", "product_id": "SKU-1", "price": 27.99, "updated_at": ts(35)},
    {"op": "c", "product_id": "SKU-2", "price": 59.99, "updated_at": ts(49)},
]

spark.createDataFrame(events).write.mode("overwrite").json(base)
spark.read.json(base).write.mode("overwrite").saveAsTable("bronze_price_changes")

spark.sql("""
  CREATE TABLE IF NOT EXISTS silver_products (product_id STRING, price DOUBLE, updated_at TIMESTAMP)
  USING DELTA
""")

spark.sql("""
  MERGE INTO silver_products AS t
  USING (
    SELECT product_id, price, updated_at, op,
           ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY updated_at DESC) AS rn
    FROM bronze_price_changes
  ) AS s
  ON t.product_id = s.product_id AND s.rn = 1
  WHEN MATCHED AND s.op = 'd' THEN DELETE
  WHEN MATCHED THEN UPDATE SET t.price = s.price, t.updated_at = s.updated_at
  WHEN NOT MATCHED AND s.op != 'd' THEN INSERT (product_id, price, updated_at)
    VALUES (s.product_id, s.price, s.updated_at)
""")

spark.sql("SELECT product_id, price, updated_at FROM silver_products ORDER BY product_id").show()
