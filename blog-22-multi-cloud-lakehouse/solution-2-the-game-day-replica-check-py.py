# Blog 22 — One Lakehouse, Three Clouds: The Multi-Cloud Finale
# Exercise 2: the game-day replica check.
# Requires: You can't rehearse three clouds from one Free Edition workspace — and this finale won't pretend otherwise. These exercises simulate the multi-cloud patterns with catalog naming and synthetic storage p

spark.sql("CREATE SCHEMA IF NOT EXISTS ops")

rows = [
    ("gold.daily_revenue",  "s3://medicore-prod/gold/daily_revenue",
     "abfss://medicore-dr/gold/daily_revenue", 1204, 1204, 5),
    ("gold.claims",         "s3://medicore-prod/gold/claims",
     "abfss://medicore-dr/gold/claims", 987, 947, 180),   # the planted stale replica
    ("silver.appointments", "s3://medicore-prod/silver/appointments",
     "abfss://medicore-dr/silver/appointments", 2100, 2100, 8),
]
(spark.createDataFrame(
    rows, ["table_name", "primary_path", "dr_path",
           "primary_log_version", "dr_log_version", "heartbeat_age_min"])
      .write.mode("overwrite").saveAsTable("ops.replica_health"))
