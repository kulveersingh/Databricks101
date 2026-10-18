# Blog 06 — Structured Streaming in Production: Beyond the Tutorial
# Exercise 3: restart drill with checkpoint vs. no checkpoint
# Requires: All three exercises run on Databricks Free Edition. There's no Kafka on Free Edition, so the streams below use the built-in `rate` source and file-based Auto Loader — the watermark, checkpoint, and `f

from pyspark.sql import functions as F

ledger_drop = "/Volumes/workspace/default/ex04_drop/ledger/"
def wave(tag, n, start):
    (spark.range(start, start + n)
        .withColumn("payment_id", F.concat(F.lit(tag), F.col("id").cast("string")))
        .withColumn("amount", ((F.col("id") % 500 + 1).cast("decimal(10,2)")))
        .drop("id")
        .write.mode("append").option("header", "true").csv(ledger_drop + tag))

wave("w1-", 400, 0)   # morning wave
# --- next cell ---

ledger = (spark.readStream.format("cloudFiles")
    .option("cloudFiles.format", "csv")
    .option("cloudFiles.schemaLocation",
             "/Volumes/workspace/default/ex04_drop/_schema/ledger")
    .option("header", "true")
    .load(ledger_drop))

# The production stream: checkpointed
(ledger.writeStream.format("delta")
    .option("checkpointLocation",
             "/Volumes/workspace/default/ex04_drop/_checkpoints/ledger")
    .trigger(availableNow=True)
    .toTable("workspace.default.ex06_ledger"))
print("After wave 1:", spark.table("workspace.default.ex06_ledger").count())

wave("w2-", 400, 400)  # afternoon wave lands while the stream is "down"

# Restart with the SAME checkpoint: resumes after the last committed file
(ledger.writeStream.format("delta")
    .option("checkpointLocation",
             "/Volumes/workspace/default/ex04_drop/_checkpoints/ledger")
    .trigger(availableNow=True)
    .toTable("workspace.default.ex06_ledger"))
print("After restart:", spark.table("workspace.default.ex06_ledger").count())
# --- next cell ---

# The failure mode: same source, FRESH checkpoint = no memory of wave 1
(ledger.writeStream.format("delta")
    .option("checkpointLocation",
             "/Volumes/workspace/default/ex04_drop/_checkpoints/ledger_fresh")
    .trigger(availableNow=True)
    .toTable("workspace.default.ex06_ledger_nocheckpoint"))
print("Fresh checkpoint table:", spark.table("workspace.default.ex06_ledger_nocheckpoint").count())
print("Duplicates:",
      spark.table("workspace.default.ex06_ledger_nocheckpoint").count()
      - spark.table("workspace.default.ex06_ledger_nocheckpoint")
            .select("payment_id").distinct().count())
