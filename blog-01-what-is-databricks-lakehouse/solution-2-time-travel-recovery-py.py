# Blog 01 — What Is Databricks, Really? The Lakehouse Explained for Builders
# Exercise 2: time travel recovery
# Requires: Everything below runs on Databricks Free Edition. All data is generated inside the notebook — nothing to download.

from pyspark.sql import functions as F

kpis = spark.createDataFrame(
    [("W40", 1200, 48000.00), ("W41", 1350, 54000.00)],
    ["week", "orders", "revenue"])
kpis.write.format("delta").mode("overwrite") \
    .saveAsTable("workspace.default.ex02_daily_kpis")

# The misconfigured job: full overwrite with raw unaggregated rows
raw = spark.createDataFrame(
    [(101, 39.99), (102, 12.50), (103, 88.00)], ["order_id", "amount"])
raw.write.format("delta").mode("overwrite") \
    .saveAsTable("workspace.default.ex02_daily_kpis")
