# Blog 03 — Delta Lake Deep Dive: ACID on Object Storage
# Exercise 2: enforcement first, evolution on purpose
# Requires: All three exercises run on Databricks Free Edition with synthetic data generated in the notebook.

from pyspark.sql import functions as F

base = (spark.range(200)
    .withColumn("sku", F.concat(F.lit("SKU-"), F.col("id")))
    .withColumn("qty", (F.col("id") % 10 + 1))
    .withColumn("price", (F.col("id") % 50 + 10).cast("decimal(10,2)"))
    .withColumn("warehouse", F.lit("west-1"))
    .drop("id"))
base.write.format("delta").mode("overwrite") \
    .saveAsTable("workspace.default.ex03b_supplier_feed")

# Normal daily file: same four columns — succeeds
base.limit(50).write.format("delta").mode("append") \
    .saveAsTable("workspace.default.ex03b_supplier_feed")

# This morning's file: surprise fifth column
drifted = base.limit(50).withColumn("discount_code", F.lit("FALL10"))
try:
    drifted.write.format("delta").mode("append") \
        .saveAsTable("workspace.default.ex03b_supplier_feed")
except Exception as e:
    print("REJECTED as expected:", str(e).split("\n")[0])
# --- next cell ---

# Business confirms the column is legitimate: deliberate evolution
(drifted.write.format("delta")
    .option("mergeSchema", "true")
    .mode("append")
    .saveAsTable("workspace.default.ex03b_supplier_feed"))

spark.sql("SELECT sku, qty, price, warehouse, discount_code FROM workspace.default.ex03b_supplier_feed").show(5)
