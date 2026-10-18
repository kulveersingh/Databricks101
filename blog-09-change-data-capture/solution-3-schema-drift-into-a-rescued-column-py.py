# Blog 09 — Change Data Capture: Streaming Your Database to the Lakehouse
# Exercise 3: Schema drift into a rescued column
# Requires: All three exercises generate their own change streams — no Debezium, no Kafka, no database required.

from pyspark.sql.functions import lit, to_json, struct
from datetime import datetime, timedelta

t0 = datetime.now().replace(microsecond=0)
def ts(hours):
    return (t0 - timedelta(hours=hours)).isoformat()

base = "/tmp/exercises/shopnest/drift"
dbutils.fs.rm(base, True)

# Batch 1: original schema
batch1 = spark.createDataFrame([
    {"op": "c", "order_id": "D001", "order_status": "placed", "updated_at": ts(50)},
    {"op": "c", "order_id": "D002", "order_status": "placed", "updated_at": ts(49)},
])
# Batch 2: source added loyalty_tier mid-stream
batch2 = spark.createDataFrame([
    {"op": "c", "order_id": "D003", "order_status": "placed", "updated_at": ts(26), "loyalty_tier": "gold"},
    {"op": "u", "order_id": "D001", "order_status": "shipped", "updated_at": ts(25), "loyalty_tier": "silver"},
])

batch1.write.mode("overwrite").json(f"{base}/batch1")
batch2.write.mode("overwrite").json(f"{base}/batch2")

# Drift detector: compare schemas across batches
b1_cols, b2_cols = set(spark.read.json(f"{base}/batch1").columns), set(spark.read.json(f"{base}/batch2").columns)
new_cols = b2_cols - b1_cols
print(f"SCHEMA DRIFT DETECTED — new columns in batch 2: {sorted(new_cols)}")
assert len(new_cols) > 0, "drift detector found nothing; check the seed data"

# Quarantine unexpected columns instead of failing or silently dropping them
bronze = spark.read.json(base)  # union of both batches
rescued = bronze.select(
    "op", "order_id", "order_status", "updated_at",
    to_json(struct(*[c for c in bronze.columns
                     if c not in ("op", "order_id", "order_status", "updated_at")])).alias("_rescued_data"),
)
rescued.createOrReplaceTempView("bronze_rescued")
