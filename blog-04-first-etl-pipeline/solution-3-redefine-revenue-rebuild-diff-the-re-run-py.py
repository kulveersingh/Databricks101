# Blog 04 — Your First ETL Pipeline: CSV to Gold in 30 Minutes
# Exercise 3: redefine revenue, rebuild, diff the re-run
# Requires: All three exercises run on Databricks Free Edition. Auto Loader (`cloudFiles`) is available on Free Edition — the source directory will be a Unity Catalog Volume, and all CSVs are generated in-noteboo

# Flag ~5% of silver orders as refunded (deterministic, so re-runs agree)
(spark.table("workspace.default.ex04_silver_orders")
    .withColumn("is_refunded", (F.hash("order_id") % 20 == 0))
    .createOrReplaceTempView("silver_flagged"))
spark.sql("""
  MERGE INTO workspace.default.ex04_silver_orders t
  USING silver_flagged s ON t.order_id = s.order_id
  WHEN MATCHED THEN UPDATE SET t.is_refunded = s.is_refunded
""")
