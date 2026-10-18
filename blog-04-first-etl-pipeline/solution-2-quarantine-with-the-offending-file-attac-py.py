# Blog 04 — Your First ETL Pipeline: CSV to Gold in 30 Minutes
# Exercise 2: quarantine with the offending file attached
# Requires: All three exercises run on Databricks Free Edition. Auto Loader (`cloudFiles`) is available on Free Edition — the source directory will be a Unity Catalog Volume, and all CSVs are generated in-noteboo

# Day 4's file: 480 valid rows + 20 bad ones from the troubled supplier
good = (spark.range(480)
    .withColumn("order_id", F.concat(F.lit("D4-"), F.col("id")))
    .withColumn("order_ts", F.lit("10:04:00"))
    .withColumn("sku", F.lit("SKU-1"))
    .withColumn("amount", F.lit("29.99").cast("decimal(10,2)"))
    .drop("id"))
bad = spark.createDataFrame(
    [(None, "10:04:00", "SKU-9", -15.00),      # null order_id
     ("D4-BAD2", "10:04:00", "SKU-9", -3.50),  # negative amount
     ("D4-BAD3", "not-a-timestamp", "SKU-9", 9.99)] * 7,  # 21 rows, bad ts
    ["order_id", "order_ts", "sku", "amount"])
good.unionByName(bad, allowMissingColumns=True) \
    .write.mode("append").option("header", "true").csv(drop)
# --- next cell ---

from pyspark.sql import Window

# Re-run bronze ingestion to pick up day 4 (checkpoint makes it incremental)
(bronze.writeStream
    .format("delta")
    .option("checkpointLocation",
             "/Volumes/workspace/default/ex04_drop/_checkpoints/bronze")
    .trigger(availableNow=True)
    .toTable("workspace.default.ex04_bronze_orders"))

silver_raw = (spark.table("workspace.default.ex04_bronze_orders")
    .withColumn("order_ts", F.to_timestamp("order_ts", "HH:mm:ss"))
    .withColumn("amount", F.col("amount").cast("decimal(10,2)"))
    .withColumn("is_valid", F.col("order_id").isNotNull()
                & (F.col("amount") > 0) & F.col("order_ts").isNotNull()))

# Bad rows go to quarantine WITH the file they came from — never just dropped
(silver_raw.filter("NOT is_valid")
    .write.format("delta").mode("append")
    .saveAsTable("workspace.default.ex04_quarantine"))

valid = silver_raw.filter("is_valid").drop("is_valid")
w = Window.partitionBy("order_id").orderBy(F.col("ingest_ts").desc())
deduped = valid.withColumn("rn", F.row_number().over(w)).filter("rn = 1").drop("rn")
deduped.createOrReplaceTempView("updates")
spark.sql("""
  MERGE INTO workspace.default.ex04_silver_orders t
  USING updates s ON t.order_id = s.order_id
  WHEN MATCHED THEN UPDATE SET *
  WHEN NOT MATCHED THEN INSERT *
""")
