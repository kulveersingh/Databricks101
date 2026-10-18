# Blog 05 — Unity Catalog: One Governance Layer to Rule Them All
# Exercise 2: dynamic view for PII masking
# Requires: Free Edition notes: catalogs, schemas, SQL grants, and dynamic views all work on Free Edition. Grant to the `account users` group below — on Free Edition, workspace-local groups can't receive Unity Ca

from pyspark.sql import functions as F
import random

random.seed(33)
names = ["Ava Chen", "Liam Ortiz", "Maya Patel", "Noah Kim", "Zoe Alvarez"]
customers = spark.createDataFrame(
    [(f"C{i:04d}", random.choice(names),
      f"user{i}@example.com", f"4111-0000-{i:04d}") for i in range(200)],
    ["customer_id", "full_name", "email", "account_no"])
customers.write.format("delta").mode("overwrite") \
    .saveAsTable("ledgerline_payments_prod.curated.customers")
