# Blog 01 — What Is Databricks, Really? The Lakehouse Explained for Builders
# Exercise 3: one table, two engines
# Requires: Everything below runs on Databricks Free Edition. All data is generated inside the notebook — nothing to download.

from pyspark.sql import functions as F
import random

random.seed(7)
clicks = spark.createDataFrame(
    [(i, random.choice(["search", "product", "cart", "checkout"]),
      random.randint(1, 500)) for i in range(20000)],
    ["event_id", "page", "user_id"])
clicks.write.format("delta").mode("overwrite") \
    .saveAsTable("workspace.default.ex03_clicks")
# --- next cell ---

# Engine 2: PySpark (what the ML feature job would run)
(spark.table("workspace.default.ex03_clicks")
    .groupBy("page").count().orderBy("page").show())
