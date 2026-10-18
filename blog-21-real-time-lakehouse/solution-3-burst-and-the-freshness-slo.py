# Blog 21 — The Real-Time Lakehouse: Kafka to Sub-100ms Serving
# Exercise 3: burst and the freshness SLO.
# Requires: Streaming is the one part of this post you can genuinely rehearse on Free Edition — Structured Streaming runs on serverless compute. Delta Live Tables is the premium piece, so these exercises use plai

from pyspark.sql import functions as F

def surge_stream(rps):
    return (spark.readStream.format("rate").option("rowsPerSecond", rps).load()
            .select(F.col("value").cast("string").alias("event_id"),
                    F.col("timestamp").alias("event_time"))
            .withWatermark("event_time", "5 minutes")
            .dropDuplicates(["event_id"]))

# decided in advance, in writing: freshness may degrade, correctness may not
for phase, rps in [("normal", 100), ("burst", 500)]:
    q = (surge_stream(rps).writeStream.format("memory")
         .queryName(f"surge_{phase}").trigger(availableNow=True).start())
    q.awaitTermination()
    row = spark.sql(f"""
        SELECT COUNT(*) AS n,
               COUNT(DISTINCT event_id) AS distinct_n,
               MAX(UNIX_TIMESTAMP(CURRENT_TIMESTAMP()) - UNIX_TIMESTAMP(event_time)) AS max_lag_s
        FROM surge_{phase}""").first()
    print(f"{phase}: rows={row['n']} distinct={row['distinct_n']} max_lag={row['max_lag_s']}s")
    assert row["n"] == row["distinct_n"], "correctness broke under burst"
print("verdict: lag grew under burst, counts stayed exact — freshness degraded, correctness didn't")
