# Blog 08 — Making Slow Queries Fast: A Databricks Tuning Playbook
# Exercise 3: Migrating a bad partition choice to Liquid Clustering
# Requires: Diagnosis is a skill you build by measuring. All three exercises generate their own data and give you before/after numbers you can quote.

from pyspark.sql.functions import expr, rand

spark.sql("DROP TABLE IF EXISTS events_partitioned")
spark.sql("DROP TABLE IF EXISTS events_clustered")

events = (
    spark.range(0, 500000)
    .withColumn("event_id", expr("uuid()"))
    .withColumn("event_date", expr("current_date() - CAST(rand() * 365 AS INT)"))
    .withColumn("customer_id", (rand() * 200000).cast("int"))
    .withColumn("event_type", expr("array('click','purchase','login')[CAST(rand() * 3 AS INT)]"))
    .withColumn("amount", (rand() * 500).cast("double"))
)

# The 2022 decision: partition by date
events.write.partitionBy("event_date").format("delta").saveAsTable("events_partitioned")

# The modern approach: liquid clustering on how queries actually filter
spark.sql("""
  CREATE TABLE events_clustered
  USING DELTA
  CLUSTER BY (customer_id, event_date)
  AS SELECT * FROM events_partitioned
""")
