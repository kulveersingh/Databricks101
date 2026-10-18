# Blog 17 — Serve Open-Source LLMs Like APIs: Llama 3 on Databricks
# Exercise 2: the A/B router and inference table.
# Requires: Databricks Free Edition for client, guardrail, and router logic. Real provisioned-throughput serving needs Premium + GPU; pay-per-token is the Free Edition path.

import random, time

rnd = random.Random(11)

def router():
    return "v4" if rnd.random() < 0.10 else "v3"   # 90/10 split

def serve(version, text):
    t0 = time.perf_counter()
    # v4: slightly better recall, slightly higher latency (simulated)
    ok = rnd.random() < (0.97 if version == "v4" else 0.93)
    time.sleep(0.001 if version == "v3" else 0.0015)
    return {"version": version, "valid": ok,
            "latency_ms": (time.perf_counter() - t0) * 1000}

inference_log = []
for i in range(1000):
    v = router()
    r = serve(v, f"form text {i}")
    inference_log.append({"request_seq": i,
                          "input_hash": abs(hash(f"form text {i}")) % 10**8,
                          "version": v, "valid": r["valid"],
                          "latency_ms": r["latency_ms"]})

spark_df = spark.createDataFrame(inference_log)
spark_df.createOrReplaceTempView("inference_log")

report = spark.sql("""
  SELECT version, COUNT(*) AS n,
         ROUND(AVG(CASE WHEN valid THEN 1.0 ELSE 0.0 END), 3) AS valid_rate,
         ROUND(percentile_approx(latency_ms, 0.95), 2) AS p95_ms
  FROM inference_log GROUP BY version
""").collect()
for row in report: print(row)
v3n = [r for r in report if r["version"] == "v3"][0]["n"]
assert 880 <= v3n <= 920, f"split drifted: v3={v3n}"
