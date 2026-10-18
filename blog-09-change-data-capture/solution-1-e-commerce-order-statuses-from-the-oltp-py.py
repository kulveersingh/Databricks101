# Blog 09 — Change Data Capture: Streaming Your Database to the Lakehouse
# Exercise 1: E-commerce order statuses from the OLTP
# Requires: All three exercises generate their own change streams — no Debezium, no Kafka, no database required.

import random
from datetime import datetime, timedelta

base = "/tmp/exercises/shopnest/order_changes"
dbutils.fs.rm(base, True)
spark.sql("DROP TABLE IF EXISTS bronze_order_changes")
spark.sql("DROP TABLE IF EXISTS silver_orders")

statuses = ["placed", "shipped", "delivered"]
events, now = [], datetime.now()

for i in range(400):
    oid = f"O{i:05d}"
    events.append({"op": "c", "order_id": oid, "order_status": "placed",
                   "updated_at": (now - timedelta(hours=30)).isoformat()})
    # most orders progress; some get cancelled (deleted upstream)
    r = random.random()
    if r < 0.7:
        events.append({"op": "u", "order_id": oid, "order_status": random.choice(["shipped", "delivered"]),
                       "updated_at": (now - timedelta(hours=random.randint(1, 20))).isoformat()})
    elif r < 0.8:
        events.append({"op": "d", "order_id": oid, "order_status": None,
                       "updated_at": (now - timedelta(hours=random.randint(1, 10))).isoformat()})

# Out-of-order: an older-dated update arriving late
events.append({"op": "u", "order_id": "O00001", "order_status": "shipped",
               "updated_at": (now - timedelta(hours=25)).isoformat()})
# Duplicate delivery of an earlier event
dup = dict(events[0])
events.append(dup)

spark.createDataFrame(events).write.mode("overwrite").json(base)
spark.read.json(base).write.mode("overwrite").saveAsTable("bronze_order_changes")
print(f"Seeded {len(events)} change events")
