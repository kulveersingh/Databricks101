# Blog 06 — Structured Streaming in Production: Beyond the Tutorial
# Exercise 1: watermarked cold-chain aggregates with late quarantine
# Requires: All three exercises run on Databricks Free Edition. There's no Kafka on Free Edition, so the streams below use the built-in `rate` source and file-based Auto Loader — the watermark, checkpoint, and `f

from pyspark.sql import functions as F

# Fixed base time: event_ts = base - delay, so "late" is deterministic
base = F.current_timestamp()

readings = (spark.readStream.format("rate")
    .option("rowsPerSecond", 200)
    .load()
    .withColumn("delay_s", (F.rand(42) * 1200).cast("int"))   # 0–20 min late
    .withColumn("event_ts", base - F.col("delay_s") * F.expr("INTERVAL 1 SECOND"))
    .withColumn("truck_id", (F.col("value") % 8).cast("string"))
    .withColumn("temp_c", 4.0 + (F.rand(7) * 3))              # reefer band ~4-7C
    .select("truck_id", "event_ts", "temp_c", "delay_s"))
# --- next cell ---

# Stream A: compliance aggregates — late data is dropped by the watermark
(windows := (readings
    .withWatermark("event_ts", "10 minutes")
    .groupBy(F.window("event_ts", "5 minutes"), "truck_id")
    .agg(F.avg("temp_c").alias("avg_temp"), F.count("*").alias("n"))
    .writeStream.format("delta")
    .option("checkpointLocation",
             "/Volumes/workspace/default/ex04_drop/_checkpoints/coldchain_win")
    .trigger(availableNow=True)
    .toTable("workspace.default.ex06_temp_windows")))
# --- next cell ---

# Stream B: quarantine — rows the watermark would drop, kept for investigation
# Late  <=>  delay_s > 600  (watermark = max(event_ts) - 10 min, event_ts = base - delay)
(readings.filter(F.col("delay_s") > 600)
    .writeStream.format("delta")
    .option("checkpointLocation",
             "/Volumes/workspace/default/ex04_drop/_checkpoints/coldchain_q")
    .trigger(availableNow=True)
    .toTable("workspace.default.ex06_temp_quarantine"))
