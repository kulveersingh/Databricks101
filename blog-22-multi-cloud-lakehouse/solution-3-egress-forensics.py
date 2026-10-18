# Blog 22 — One Lakehouse, Three Clouds: The Multi-Cloud Finale
# Exercise 3: egress forensics.
# Requires: You can't rehearse three clouds from one Free Edition workspace — and this finale won't pretend otherwise. These exercises simulate the multi-cloud patterns with catalog naming and synthetic storage p

spark.sql("CREATE SCHEMA IF NOT EXISTS finops")

EGRESS_PER_GB = 0.09  # illustrative — plug in your cloud's current per-GB rate
flows = [
    ("gcp-training_reads_aws_gold", "aws", "gcp", 850.0),  # the chatty one
    ("azure-dr_replication",        "aws", "azure", 120.0),
    ("bi_extract_to_azure",         "aws", "azure", 15.0),
]
rows = [(name, src, dst, gb, gb * EGRESS_PER_GB * 30) for name, src, dst, gb in flows]
(spark.createDataFrame(rows, ["flow", "src", "dst", "gb_per_day", "usd_per_month"])
      .write.mode("overwrite").saveAsTable("finops.cross_cloud_flows"))

spark.sql("""SELECT flow, gb_per_day, ROUND(usd_per_month, 2) AS usd_per_month
             FROM finops.cross_cloud_flows ORDER BY usd_per_month DESC""").show(truncate=False)
