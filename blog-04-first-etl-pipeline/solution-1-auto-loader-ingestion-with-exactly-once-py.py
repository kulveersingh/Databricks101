# Blog 04 — Your First ETL Pipeline: CSV to Gold in 30 Minutes
# Exercise 1: Auto Loader ingestion with exactly-once re-runs
# Requires: All three exercises run on Databricks Free Edition. Auto Loader (`cloudFiles`) is available on Free Edition — the source directory will be a Unity Catalog Volume, and all CSVs are generated in-noteboo

from pyspark.sql import functions as F
import random

random.seed(21)
drop = "/Volumes/workspace/default/ex04_drop/orders/"

# Three "daily" CSV drops, 500 orders each
for day in (1, 2, 3):
    (spark.range(500)
        .withColumn("order_id", F.concat(F.lit(f"D{day}-"), F.col("id")))
        .withColumn("order_ts", F.lit(f"10:{day:02d}:00").cast("string"))
        .withColumn("sku", F.concat(F.lit("SKU-"), (F.col("id") % 50).cast("string")))
        .withColumn("amount", ((F.col("id") % 200 + 5).cast("decimal(10,2)")))
        .drop("id")
        .write.mode("append").option("header", "true")
        .csv(drop))
# --- next cell ---

bronze = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "csv")
    .option("cloudFiles.schemaLocation",
             "/Volumes/workspace/default/ex04_drop/_schema/orders")
    .option("header", "true")
    .load(drop)
    .withColumn("ingest_ts", F.current_timestamp())
    .withColumn("source_file", F.col("_metadata.file_path")))

(bronze.writeStream
    .format("delta")
    .option("checkpointLocation",
             "/Volumes/workspace/default/ex04_drop/_checkpoints/bronze")
    .trigger(availableNow=True)
    .toTable("workspace.default.ex04_bronze_orders"))
# --- next cell ---

# Prove the re-run is boring: run the exact same stream again
(bronze.writeStream
    .format("delta")
    .option("checkpointLocation",
             "/Volumes/workspace/default/ex04_drop/_checkpoints/bronze")
    .trigger(availableNow=True)
    .toTable("workspace.default.ex04_bronze_orders"))

print("Bronze row count:", spark.table("workspace.default.ex04_bronze_orders").count())
print("Distinct source files:", spark.table("workspace.default.ex04_bronze_orders")
      .select("source_file").distinct().count())
