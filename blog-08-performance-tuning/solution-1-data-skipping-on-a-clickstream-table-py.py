# Blog 08 — Making Slow Queries Fast: A Databricks Tuning Playbook
# Exercise 1: Data skipping on a clickstream table
# Requires: Diagnosis is a skill you build by measuring. All three exercises generate their own data and give you before/after numbers you can quote.

from pyspark.sql.functions import col, rand, randn, datediff, current_date, expr

spark.sql("DROP TABLE IF EXISTS clickstream")
countries = ["US", "CA", "GB", "DE", "FR", "AU"]

# Write in many small batches to simulate streaming ingestion
for batch in range(60):
    df = (
        spark.range(0, 35000)
        .withColumn("event_id", expr("uuid()"))
        .withColumn("event_date", expr(f"current_date() - CAST(rand() * 90 AS INT)"))
        .withColumn("country", expr(f"array({','.join(repr(c) for c in countries)})[CAST(rand() * 6 AS INT)]"))
        .withColumn("user_id", (rand() * 500000).cast("int"))
        .withColumn("url", expr("concat('/page/', CAST(CAST(rand() * 1000 AS INT) AS STRING))"))
        .withColumn("dwell_seconds", (randn() * 30 + 60).cast("double"))
    )
    df.write.mode("append").format("delta").saveAsTable("clickstream")

spark.sql("DESCRIBE DETAIL clickstream").select("numFiles").show()
