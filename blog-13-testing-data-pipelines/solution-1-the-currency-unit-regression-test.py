# Blog 13 — Testing Data Pipelines: Unit, Integration, and Data Quality Tests
# Exercise 1: the currency-unit regression test.
# Requires: Plain Spark session (local or Databricks Free Edition); no cluster, no DBU spend. Real @dlt.expect_or_drop needs a Premium workspace — the exercises emulate its logic.

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import random

spark = SparkSession.builder.master("local[2]").appName("ex13-1").getOrCreate()

def gen_orders(n, unit="dollars", seed=42):
    rnd = random.Random(seed)
    # sentinel row: $42.50 must ALWAYS become 4250 cents — this is what
    # catches the provider silently switching units
    rows = [("SENTINEL", 42.50)]
    for i in range(n):
        oid = f"O{i:06d}"
        amt = round(rnd.uniform(5, 500), 2)
        if rnd.random() < 0.02:      # duplicates
            rows.append((oid, amt))
        if rnd.random() < 0.01:      # null keys
            rows.append((None, amt))
        rows.append((oid, amt if unit == "dollars" else int(amt * 100)))
    return spark.createDataFrame(rows, ["order_id", "amount"])

def clean_orders(df):
    """Assumes amount is in dollars; normalizes to cents."""
    return (df.dropna(subset=["order_id"])
              .dropDuplicates(["order_id"])
              .withColumn("amount_cents", (col("amount") * 100).cast("long")))

def test_clean_orders():
    out = clean_orders(gen_orders(5000, unit="dollars"))
    sentinel = out.filter(col("order_id") == "SENTINEL").collect()[0]
    assert sentinel["amount_cents"] == 4250, \
        f"conversion broken: SENTINEL amount became {sentinel['amount_cents']} cents"
    assert out.filter(col("order_id").isNull()).count() == 0
    assert out.groupBy("order_id").count().filter(col("count") > 1).count() == 0

test_clean_orders()   # passes on dollars
