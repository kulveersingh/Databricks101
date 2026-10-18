# Blog 08 — Making Slow Queries Fast: A Databricks Tuning Playbook
# Exercise 2: The daily OPTIMIZE job
# Requires: Diagnosis is a skill you build by measuring. All three exercises generate their own data and give you before/after numbers you can quote.

from pyspark.sql.functions import expr, rand

spark.sql("DROP TABLE IF EXISTS silver_orders")

for batch in range(30):
    df = (
        spark.range(0, 1700)
        .withColumn("order_id", expr("uuid()"))
        .withColumn("order_date", expr("current_date() - CAST(rand() * 45 AS INT)"))
        .withColumn("store_id", (rand() * 40).cast("int"))
        .withColumn("amount", (rand() * 200 + 5).cast("double"))
    )
    df.write.mode("append").format("delta").saveAsTable("silver_orders")

spark.sql("DESCRIBE DETAIL silver_orders").select("numFiles").show()
