# Blog 13 — Testing Data Pipelines: Unit, Integration, and Data Quality Tests
# Exercise 2: quarantine, don't silently drop.
# Requires: Plain Spark session (local or Databricks Free Edition); no cluster, no DBU spend. Real @dlt.expect_or_drop needs a Premium workspace — the exercises emulate its logic.

from pyspark.sql.functions import col, lit, when

def ingest_with_quarantine(df):
    is_int_id = col("customer_id").rlike(r"^\d+$")
    clean = df.filter(col("customer_id").isNotNull() & is_int_id)
    quarantine = (df.filter(~(col("customer_id").isNotNull() & is_int_id))
                    .withColumn("_violation", lit("customer_id not integer")))
    return clean, quarantine

# fixture: 950 integer ids, 50 UUID strings, 2 nulls
import uuid
rows = [(f"{i}", 10.0) for i in range(950)]
rows += [(str(uuid.uuid4()), 10.0) for _ in range(50)]
rows += [(None, 5.0), (None, 7.5)]
df = spark.createDataFrame(rows, ["customer_id", "amount"])

clean, quarantine = ingest_with_quarantine(df)
assert clean.count() == 950, clean.count()
q = quarantine.collect()
assert len(q) == 52, len(q)          # 50 UUIDs + 2 nulls
assert all(r["_violation"] == "customer_id not integer" for r in q)
print(f"clean={clean.count()} quarantined={len(q)}")
