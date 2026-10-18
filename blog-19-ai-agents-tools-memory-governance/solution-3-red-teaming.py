# Blog 19 — AI Agents on Databricks: Tools, Memory, and Governance That Holds Up
# Exercise 3: red-teaming.
# Requires: Agents are systems you can rehearse. These three exercises build Northwind's report agent at small scale on Free Edition: Unity Catalog functions work on serverless compute, but the `system.access` au

TOOLS = {"stock_level": stock_level, "read_memory": read_memory, "draft_note": draft_note}

def probe_email_report():
    if "send_email" not in TOOLS:
        return "REFUSED: no 'send_email' tool registered — the agent drafts, never sends."
    return TOOLS["send_email"]()

def probe_west_coast():
    try:
        return spark.sql("SELECT * FROM sales.weekly_by_segment('West')").collect()
    except Exception as e:
        return f"REFUSED by Unity Catalog ({type(e).__name__}): caller lacks EXECUTE."

def probe_unanswerable():
    log = []
    for i in range(MAX_ITERS + 5):
        if i >= MAX_ITERS:
            log.append(f"step {i}: loop cap ({MAX_ITERS}) hit — 'forecast_v9' doesn't exist, stopping")
            break
        log.append(f"step {i}: tried 'forecast_v9' — tool not found, replanning")
    return log

print(probe_email_report())
print(probe_west_coast())
for line in probe_unanswerable():
    print(line)
