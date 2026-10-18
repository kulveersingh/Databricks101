# Blog 03 — Delta Lake Deep Dive: ACID on Object Storage
# Exercise 3: restore after the bad backfill
# Requires: All three exercises run on Databricks Free Edition with synthetic data generated in the notebook.

revenue = spark.createDataFrame(
    [("apparel", 12000.00), ("home", 8500.00), ("outdoor", 15200.00)],
    ["category", "revenue"])
revenue.write.format("delta").mode("overwrite") \
    .saveAsTable("workspace.default.ex03b_order_revenue")

good_version = spark.sql(
    "DESCRIBE HISTORY workspace.default.ex03b_order_revenue") \
    .select("version").first()["version"]

# The bad backfill: cents instead of dollars
(spark.table("workspace.default.ex03b_order_revenue")
    .withColumn("revenue", F.col("revenue") * 100)
    .write.format("delta").mode("overwrite")
    .saveAsTable("workspace.default.ex03b_order_revenue"))
