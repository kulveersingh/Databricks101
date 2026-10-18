# Blog 01 — What Is Databricks, Really? The Lakehouse Explained for Builders
# Exercise 1: reading the transaction log
# Requires: Everything below runs on Databricks Free Edition. All data is generated inside the notebook — nothing to download.

from pyspark.sql import functions as F

# 1. Synthetic vendor catalog: 5,000 SKUs
products = (spark.range(5000)
    .withColumn("sku", F.concat(F.lit("SKU-"), F.col("id")))
    .withColumn("category", F.when(F.col("id") % 3 == 0, "apparel")
                .when(F.col("id") % 3 == 1, "home").otherwise("outdoor"))
    .withColumn("price", (F.col("id") % 200 + 5).cast("decimal(10,2)"))
    .drop("id"))

products.write.format("delta").mode("overwrite") \
    .saveAsTable("workspace.default.ex01_vendor_catalog")

# 2a. Write 2: vendor reprices 500 items
(spark.table("workspace.default.ex01_vendor_catalog")
    .withColumn("price", F.col("price") * F.lit("1.10"))
    .limit(500)
    .createOrReplaceTempView("repriced"))
spark.sql("""
  MERGE INTO workspace.default.ex01_vendor_catalog t
  USING repriced s ON t.sku = s.sku
  WHEN MATCHED THEN UPDATE SET t.price = s.price
""")

# 2b. Write 3: vendor silently drops the whole "outdoor" category
spark.sql("DELETE FROM workspace.default.ex01_vendor_catalog WHERE category = 'outdoor'")
# --- next cell ---

# Read the raw log: one JSON file per committed version
detail = spark.sql("DESCRIBE DETAIL workspace.default.ex01_vendor_catalog") \
    .select("location").first()["location"]
log = spark.read.json(detail + "/_delta_log/*.json")

# Every remove action = files (and their rows) that left the table in that version
from pyspark.sql import functions as F
(log.filter("remove IS NOT NULL")
    .select(F.input_file_name().alias("log_file"),
            "remove.deletionTimestamp", "add.numRecords")
    .show(truncate=False))
