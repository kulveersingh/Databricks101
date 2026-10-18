# Blog 19 — AI Agents on Databricks: Tools, Memory, and Governance That Holds Up
# Exercise 1: the governed tool.
# Requires: Agents are systems you can rehearse. These three exercises build Northwind's report agent at small scale on Free Edition: Unity Catalog functions work on serverless compute, but the `system.access` au

import numpy as np

rng = np.random.default_rng(21)
spark.sql("CREATE SCHEMA IF NOT EXISTS sales")

regions = ["Midwest", "West", "South", "Northeast"]
segments = ["industrial", "retail", "saas"]
rows = []
for r in regions:
    for s in segments:
        for _ in range(200):
            churn_p = 0.11 if (r == "Midwest" and s == "industrial") else 0.08
            rows.append((r, s, "Q3", int(rng.random() < churn_p),
                         float(rng.uniform(20000, 200000))))

(spark.createDataFrame(rows, ["region", "segment", "quarter", "churned", "arr"])
      .write.mode("overwrite").saveAsTable("sales.customer_monthly"))
# --- next cell ---

# the agent's tool call — one step of the plan → call → observe loop
midwest = spark.sql("SELECT * FROM sales.weekly_by_segment('Midwest')")
midwest.show()
# A principal outside `analysts` running the same call gets a permission error.
# Test it by revoking first — the denial, not the success, is the feature.
