# Blog 21 — The Real-Time Lakehouse: Kafka to Sub-100ms Serving
# Exercise 2: exactly-once under redelivery.
# Requires: Streaming is the one part of this post you can genuinely rehearse on Free Edition — Structured Streaming runs on serverless compute. Delta Live Tables is the premium piece, so these exercises use plai

from pyspark.sql import functions as F

spark.sql("CREATE SCHEMA IF NOT EXISTS realtime")

raw = (spark.readStream.format("rate").option("rowsPerSecond", 100).load()
       .select(F.col("value").cast("string").alias("event_id"),
               (F.col("value") % 50).cast("string").alias("card_id"),
               F.col("timestamp").alias("event_time")))
redelivered = raw.union(raw)  # Kafka redelivery after a consumer restart

silver = (redelivered
          .withWatermark("event_time", "5 minutes")
          .dropDuplicates(["event_id"]))

spark.sql("""CREATE TABLE IF NOT EXISTS realtime.card_events
             (event_id STRING, card_id STRING, event_time TIMESTAMP) USING DELTA""")

def upsert(batch_df, _batch_id):
    batch_df.createOrReplaceTempView("batch")
    spark.sql("""MERGE INTO realtime.card_events t
                 USING batch s ON t.event_id = s.event_id
                 WHEN NOT MATCHED THEN INSERT *""")

q = (silver.writeStream.foreachBatch(upsert)
     .option("checkpointLocation", "/Volumes/main/default/checkpoints/card-events")
     .trigger(availableNow=True).start())  # <-- point at a UC Volume you own
q.awaitTermination()

n_total = spark.sql("SELECT COUNT(*) c FROM realtime.card_events").first()["c"]
n_distinct = spark.sql("SELECT COUNT(DISTINCT event_id) c FROM realtime.card_events").first()["c"]
print(f"rows={n_total} distinct event_ids={n_distinct}")
assert n_total == n_distinct, "duplicate counted twice — exactly-once broken"
print("exactly-once holds: restart the query on the same checkpoint and both numbers stay put")
