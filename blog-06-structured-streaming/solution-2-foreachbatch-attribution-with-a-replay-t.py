# Blog 06 — Structured Streaming in Production: Beyond the Tutorial
# Exercise 2: `foreachBatch` attribution with a replay test
# Requires: All three exercises run on Databricks Free Edition. There's no Kafka on Free Edition, so the streams below use the built-in `rate` source and file-based Auto Loader — the watermark, checkpoint, and `f

from pyspark.sql import functions as F
import random

random.seed(55)
# Static purchase history: some users buy within 15 min of "now"
purchases = spark.createDataFrame(
    [(f"u{i%50}", f"p{i%20}", i) for i in range(300)],
    ["user_id", "product_id", "minutes_ago"])
purchases.write.format("delta").mode("overwrite") \
    .saveAsTable("workspace.default.ex06_purchases")

spark.sql("""
  CREATE TABLE IF NOT EXISTS workspace.default.ex06_attribution (
    click_id STRING, user_id STRING, product_id STRING,
    purchase_id STRING, batch_id BIGINT)
  USING DELTA""")

def attribute_and_upsert(batch_df, batch_id):
    # Clicks from this micro-batch, joined to purchases within 15 min
    attributed = (batch_df
        .join(spark.table("workspace.default.ex06_purchases"),
              on=["user_id", "product_id"], how="inner")
        .withColumn("purchase_id", F.concat(F.col("user_id"), F.lit("-buy")))
        .withColumn("batch_id", F.lit(batch_id))
        .select("click_id", "user_id", "product_id", "purchase_id", "batch_id"))
    attributed.createOrReplaceTempView("attrib_updates")
    spark.sql(f"""
      MERGE INTO workspace.default.ex06_attribution t
      USING attrib_updates s ON t.click_id = s.click_id
      WHEN MATCHED THEN UPDATE SET *
      WHEN NOT MATCHED THEN INSERT *""")

clicks = (spark.readStream.format("rate").option("rowsPerSecond", 100).load()
    .withColumn("click_id", F.concat(F.lit("c"), F.col("value").cast("string")))
    .withColumn("user_id", F.concat(F.lit("u"), (F.col("value") % 50).cast("string")))
    .withColumn("product_id", F.concat(F.lit("p"), (F.col("value") % 20).cast("string")))
    .select("click_id", "user_id", "product_id"))

(clicks.writeStream
    .foreachBatch(attribute_and_upsert)
    .option("checkpointLocation",
             "/Volumes/workspace/default/ex04_drop/_checkpoints/attrib")
    .trigger(availableNow=True)
    .start().awaitTermination())
# --- next cell ---

# Crash-replay simulation: same batch_id, same data, invoked twice
replay_df = spark.createDataFrame(
    [("c1", "u1", "p1"), ("c2", "u2", "p2")],
    ["click_id", "user_id", "product_id"])
before = spark.table("workspace.default.ex06_attribution").count()
attribute_and_upsert(replay_df, 999)   # first attempt commits...
attribute_and_upsert(replay_df, 999)   # ...replay after the "crash"
after = spark.table("workspace.default.ex06_attribution").count()
print(f"rows before replay: {before}, after two invocations: {after}")
# after - before is at most 2 (the two new click_ids), never 4
