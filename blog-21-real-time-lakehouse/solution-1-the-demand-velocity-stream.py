# Blog 21 — The Real-Time Lakehouse: Kafka to Sub-100ms Serving
# Exercise 1: the demand-velocity stream.
# Requires: Streaming is the one part of this post you can genuinely rehearse on Free Edition — Structured Streaming runs on serverless compute. Delta Live Tables is the premium piece, so these exercises use plai

from pyspark.sql import functions as F
import time

spark.sql("CREATE SCHEMA IF NOT EXISTS realtime")

events = (
    spark.readStream.format("rate").option("rowsPerSecond", 200).load()
    .withColumn("event_id", F.col("value").cast("string"))
    .withColumn("product_id", (F.col("value") % 100).cast("string"))
    .withColumn("event_type",
                F.when(F.col("value") % 10 == 0, "purchase")
                 .when(F.col("value") % 3 == 0, "cart_add").otherwise("view"))
    .withColumn("qty", F.when(F.col("value") % 97 == 0, F.lit(-1)).otherwise(F.lit(1)))
    .withColumn("product_id",
                F.when(F.col("value") % 89 == 0, F.lit(None)).otherwise(F.col("product_id")))
    .withColumn("event_time", F.col("timestamp"))
    .select("event_id", "product_id", "event_type", "qty", "event_time")
)

silver = (events
    .withWatermark("event_time", "10 minutes")
    .dropDuplicates(["event_id"])
    .filter(F.col("product_id").isNotNull() & (F.col("qty") > 0)))

quarantine = events.filter(F.col("product_id").isNull() | (F.col("qty") <= 0))

velocity = (silver
    .groupBy(F.window("event_time", "15 minutes"), "product_id")
    .count().withColumnRenamed("count", "demand_velocity"))

q_silver = silver.writeStream.outputMode("append").format("memory").queryName("silver_events").start()
q_vel = velocity.writeStream.outputMode("complete").format("memory").queryName("demand_velocity").start()
q_quar = quarantine.writeStream.outputMode("append").format("memory").queryName("quarantine").start()

time.sleep(60)  # let a few micro-batches run

bad_in_silver = spark.sql(
    "SELECT COUNT(*) c FROM silver_events WHERE product_id IS NULL OR qty <= 0").first()["c"]
print("velocity rows:", spark.sql("SELECT COUNT(*) c FROM demand_velocity").first()["c"])
print("quarantined:", spark.sql("SELECT COUNT(*) c FROM quarantine").first()["c"])
assert bad_in_silver == 0, "malformed event reached silver"
print("silver is clean: malformed events were quarantined, not dropped silently")

for q in (q_silver, q_vel, q_quar):
    q.stop()
