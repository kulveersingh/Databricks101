# Blog 13 — Testing Data Pipelines: Unit, Integration, and Data Quality Tests
# Exercise 3: deterministic adversarial fixtures.
# Requires: Plain Spark session (local or Databricks Free Edition); no cluster, no DBU spend. Real @dlt.expect_or_drop needs a Premium workspace — the exercises emulate its logic.

import random
from pyspark.sql.functions import col

def gen_adversarial(n, badness=0.05, seed=42):
    rnd = random.Random(seed)
    rows = []
    for i in range(n):
        bad = rnd.random() < badness
        oid = None if (bad and rnd.random() < 0.3) else f"O{i:06d}"
        amt = rnd.uniform(-5000, 50000) if bad else round(rnd.uniform(5, 500), 2)
        name = "José Müller ☃" if (bad and rnd.random() < 0.2) else f"Customer {i}"
        rows.append((oid, amt, name))
    return spark.createDataFrame(rows, ["order_id", "amount", "name"])

def quality_check(df):
    total = df.count()
    return {
        "null_order_id_rate": df.filter(col("order_id").isNull()).count() / total,
        "negative_amount_rate": df.filter(col("amount") < 0).count() / total,
    }

# determinism: same seed -> identical rows
a = gen_adversarial(10000, seed=7).collect()
b = gen_adversarial(10000, seed=7).collect()
assert [tuple(r) for r in a] == [tuple(r) for r in b]

# adversarial: raise the badness and watch the check trip
ok = quality_check(gen_adversarial(10000, badness=0.01))
bad = quality_check(gen_adversarial(10000, badness=0.20))
assert ok["null_order_id_rate"] < 0.05 < bad["null_order_id_rate"]
print("clean-day:", ok, "| worst-day:", bad)
