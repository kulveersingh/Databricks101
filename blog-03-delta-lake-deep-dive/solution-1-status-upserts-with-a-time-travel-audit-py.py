# Blog 03 — Delta Lake Deep Dive: ACID on Object Storage
# Exercise 1: status upserts with a time-travel audit trail
# Requires: All three exercises run on Databricks Free Edition with synthetic data generated in the notebook.

from pyspark.sql import functions as F
import random

random.seed(11)
statuses = ["placed"] * 1000
orders = spark.createDataFrame(
    [(i, "placed", i) for i in range(1000)], ["order_id", "status", "status_ts"])
orders.write.format("delta").mode("overwrite") \
    .saveAsTable("workspace.default.ex03b_orders")

def feed(updates):
    df = spark.createDataFrame(updates, ["order_id", "status", "status_ts"])
    df.createOrReplaceTempView("feed")
    spark.sql("""
      MERGE INTO workspace.default.ex03b_orders t
      USING feed s ON t.order_id = s.order_id
      WHEN MATCHED THEN UPDATE SET t.status = s.status, t.status_ts = s.status_ts
    """)

# Warehouse feed 1: 300 orders ship
feed([(i, "shipped", 1000 + i) for i in random.sample(range(1000), 300)])
# Warehouse feed 2: 150 of those deliver (disputed order 42 among them)
shipped = [r.order_id for r in spark.sql(
    "SELECT order_id FROM workspace.default.ex03b_orders WHERE status = 'shipped'").collect()]
feed([(i, "delivered", 2000 + i) for i in shipped[:150]])
