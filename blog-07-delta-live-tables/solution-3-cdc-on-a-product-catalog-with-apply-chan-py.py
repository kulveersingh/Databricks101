# Blog 07 — Delta Live Tables: Declarative Pipelines That Fix Themselves
# Exercise 3: CDC on a product catalog with apply_changes
# Requires: Time to get your hands dirty. All three exercises generate their own data — no downloads, no external services.

base = "/tmp/exercises/streamcart/product_changes"
dbutils.fs.rm(base, True)

from datetime import datetime, timedelta
t0 = datetime.now().replace(microsecond=0)

def ts(hours):
    return (t0 - timedelta(hours=hours)).isoformat()

events = [
    # inserts
    {"op": "c", "product_id": "P1", "price": 19.99, "updated_at": ts(72)},
    {"op": "c", "product_id": "P2", "price": 49.99, "updated_at": ts(71)},
    {"op": "c", "product_id": "P3", "price": 9.99,  "updated_at": ts(70)},
    # price update arrives BEFORE an older-dated correction (out of order)
    {"op": "u", "product_id": "P1", "price": 24.99, "updated_at": ts(30)},
    {"op": "u", "product_id": "P1", "price": 22.99, "updated_at": ts(48)},
    # duplicate delivery of the P2 insert (Kafka redelivery)
    {"op": "c", "product_id": "P2", "price": 49.99, "updated_at": ts(71)},
    # P3 discontinued
    {"op": "d", "product_id": "P3", "price": None,  "updated_at": ts(5)},
]

spark.createDataFrame(events).write.mode("overwrite").json(base)
# --- next cell ---

import dlt
from pyspark.sql.functions import expr

@dlt.table(comment="Raw product change events, append-only")
def bronze_product_changes():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .load("/tmp/exercises/streamcart/product_changes")
    )

dlt.create_target_streaming_table("silver_products")

dlt.apply_changes(
    target="silver_products",
    source="bronze_product_changes",
    keys=["product_id"],
    sequence_by="updated_at",
    apply_as_deletes=expr("op = 'd'"),
    except_column_list=["op"],
)
