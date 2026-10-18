# Blog 19 — AI Agents on Databricks: Tools, Memory, and Governance That Holds Up
# Exercise 2: the loop, memory, and the missing tool.
# Requires: Agents are systems you can rehearse. These three exercises build Northwind's report agent at small scale on Free Edition: Unity Catalog functions work on serverless compute, but the `system.access` au

spark.sql("CREATE SCHEMA IF NOT EXISTS inventory")
spark.sql("CREATE SCHEMA IF NOT EXISTS agent")
spark.sql("CREATE SCHEMA IF NOT EXISTS reports")

(spark.createDataFrame([("SKU-001", "store-42", 12), ("SKU-002", "store-42", 45),
                        ("SKU-003", "store-42", 7)], ["sku", "store", "qty"])
      .write.mode("overwrite").saveAsTable("inventory.stock"))
(spark.createDataFrame([("reorder_threshold", "20")], ["key", "value"])
      .write.mode("overwrite").saveAsTable("agent.memory"))

def stock_level(sku):
    row = spark.sql(f"SELECT qty FROM inventory.stock WHERE sku = '{sku}' "
                    f"AND store = 'store-42'").first()
    return {"sku": sku, "qty": row["qty"] if row else None}

def read_memory(key):
    row = spark.sql(f"SELECT value FROM agent.memory WHERE key = '{key}'").first()
    return row["value"] if row else None

def draft_note(title, body):
    (spark.createDataFrame([(title, body)], ["title", "body"])
          .write.mode("append").saveAsTable("reports.drafts"))
    return f"draft saved: {title}"

MAX_ITERS = 10

def agent_run():
    trace = []
    threshold = int(read_memory("reorder_threshold"))   # long-term memory, via a tool call
    trace.append(("read_memory", "reorder_threshold", threshold))
    low = []
    for sku in ["SKU-001", "SKU-002", "SKU-003"]:
        if len(trace) >= MAX_ITERS:                     # the loop cap
            trace.append(("cap", "max iterations reached", None))
            break
        obs = stock_level(sku)
        trace.append(("stock_level", sku, obs["qty"]))
        if obs["qty"] is not None and obs["qty"] < threshold:
            low.append((sku, obs["qty"]))
    body = "SKUs below threshold (20) at store-42: " + \
           ", ".join(f"{s} (qty {q})" for s, q in low)
    draft_note("store-42 reorder draft", body)
    trace.append(("draft_note", "store-42 reorder draft", body))
    # your own audit log — system.access.audit is premium; this table is yours
    (spark.createDataFrame(
        [(i, tool, str(args), str(obs)) for i, (tool, args, obs) in enumerate(trace)],
        ["step", "tool", "args", "observation"])
          .write.mode("append").saveAsTable("agent.trace_log"))
    return body

print(agent_run())
spark.sql("SELECT * FROM reports.drafts").show(truncate=False)
