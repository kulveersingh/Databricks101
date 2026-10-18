# Blog 07 — Delta Live Tables: Declarative Pipelines That Fix Themselves
# Exercise 1: Quality-gated airline bookings
# Requires: Time to get your hands dirty. All three exercises generate their own data — no downloads, no external services.

import json, random
from datetime import datetime, timedelta

base = "/tmp/exercises/skyroute/bookings"
dbutils.fs.rm(base, True)

rows = []
for i in range(5000):
    bad_passenger = random.random() < 0.01
    bad_amount = random.random() < 0.005
    rows.append({
        "booking_id": f"BK{i:06d}",
        "passenger_id": None if bad_passenger else f"P{random.randint(1, 2000):05d}",
        "flight_id": f"SR{random.randint(100, 999)}",
        "amount": -round(random.uniform(10, 500), 2) if bad_amount else round(random.uniform(50, 1200), 2),
        "booking_ts": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
    })

spark.createDataFrame(rows).write.mode("overwrite").json(base)
print(f"Seeded {len(rows)} booking events")
# --- next cell ---

import dlt

@dlt.table(comment="Raw SkyRoute booking events, as they arrived")
def bronze_bookings():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .load("/tmp/exercises/skyroute/bookings")
    )

rules = {
    "booking_id_present": "booking_id IS NOT NULL",
    "passenger_present": "passenger_id IS NOT NULL",
    "flight_present": "flight_id IS NOT NULL",
}

@dlt.table(comment="Quality-gated bookings")
@dlt.expect_all_or_drop(rules)
@dlt.expect_or_fail("non_negative_amount", "amount >= 0")
def silver_bookings():
    return dlt.read_stream("bronze_bookings")
# --- next cell ---

bronze = spark.read.json("/tmp/exercises/skyroute/bookings")

# expect_all_or_drop, simulated: quarantine bad rows, keep them in bronze
clean = bronze.filter(
    "booking_id IS NOT NULL AND passenger_id IS NOT NULL AND flight_id IS NOT NULL"
)
print(f"Dropped by expectations: {bronze.count() - clean.count()}")

# expect_or_fail, simulated: stop before publishing
bad_amounts = clean.filter("amount < 0").count()
assert bad_amounts == 0, f"expect_or_fail would stop the pipeline: {bad_amounts} negative amounts"

clean.write.mode("overwrite").saveAsTable("skyroute_silver_bookings")
