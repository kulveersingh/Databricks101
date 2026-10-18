# Blog 07 — Delta Live Tables: Declarative Pipelines That Fix Themselves
# Exercise 2: Expect vs. expect_or_drop vs. expect_or_fail
# Requires: Time to get your hands dirty. All three exercises generate their own data — no downloads, no external services.

import random

base = "/tmp/exercises/citytrips/trips"
dbutils.fs.rm(base, True)

rows = []
for i in range(3000):
    zero_dist = random.random() < 0.03
    neg_fare = random.random() < 0.004
    rows.append({
        "trip_id": f"T{i:06d}",
        "trip_distance": 0.0 if zero_dist else round(random.uniform(0.5, 25.0), 2),
        "fare_amount": -round(random.uniform(5, 60), 2) if neg_fare else round(random.uniform(4, 90), 2),
    })

spark.createDataFrame(rows).write.mode("overwrite").json(base)
# --- next cell ---

import dlt

@dlt.table(comment="Raw trip records")
def bronze_trips():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .load("/tmp/exercises/citytrips/trips")
    )

# 1. Record only: rows stay, metric is logged
@dlt.table(comment="Trips, distance expectation recorded")
@dlt.expect("positive_distance", "trip_distance > 0")
def silver_trips_recorded():
    return dlt.read_stream("bronze_trips")

# 2. Quarantine: bad rows dropped from this table, kept in bronze
@dlt.table(comment="Trips, zero-distance quarantined")
@dlt.expect_or_drop("positive_distance", "trip_distance > 0")
def silver_trips_quarantined():
    return dlt.read_stream("bronze_trips")

# 3. Stop: a negative fare halts the pipeline
@dlt.table(comment="Trips, negative fare is a hard stop")
@dlt.expect_or_fail("non_negative_fare", "fare_amount >= 0")
def silver_trips_guarded():
    return dlt.read_stream("bronze_trips")
# --- next cell ---

bronze = spark.read.json("/tmp/exercises/citytrips/trips")
total = bronze.count()

recorded_bad = bronze.filter("trip_distance <= 0").count()   # expect: just record
print(f"expect would record {recorded_bad}/{total} bad-distance rows")

quarantined = bronze.filter("trip_distance > 0")              # expect_or_drop
print(f"expect_or_drop keeps {quarantined.count()}/{total} rows")

guarded_bad = bronze.filter("fare_amount < 0").count()        # expect_or_fail
assert guarded_bad == 0, f"expect_or_fail would stop the pipeline ({guarded_bad} bad fares)"
