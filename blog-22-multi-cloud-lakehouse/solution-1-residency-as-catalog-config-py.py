# Blog 22 — One Lakehouse, Three Clouds: The Multi-Cloud Finale
# Exercise 1: residency as catalog config.
# Requires: You can't rehearse three clouds from one Free Edition workspace — and this finale won't pretend otherwise. These exercises simulate the multi-cloud patterns with catalog naming and synthetic storage p

import numpy as np

rng = np.random.default_rng(41)
for catalog in ("eu_customers", "us_customers"):
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.patients")
    n = 500 if catalog == "eu_customers" else 2000
    rows = [(f"p-{i:05d}", catalog.split("_")[0], int(rng.integers(18, 90)))
            for i in range(n)]
    (spark.createDataFrame(rows, ["patient_id", "region", "age"])
          .write.mode("overwrite").saveAsTable(f"{catalog}.patients.records"))
