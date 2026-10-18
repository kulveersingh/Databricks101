# Blog 12 — CI/CD for Data Pipelines with GitHub Actions
# Exercise 1: The lint gate catches the Friday-afternoon edit
# Requires: Everything here runs locally — a repo directory, `ruff`/`pytest`, and YAML files. No workspace needed.

import json  # unused import: ruff F401

def clean_orders(rows):
    cleaned = []
    for r in rows:
        total = r["total"]
        if total is None or total < 0:
            continue
        cleaned.append({"order_id": r["order_id"], "total": total})
    return cleaned

def summarize(cleaned):
    return {"count": len(cleaned), "revenue": sum(r["total"] for r in cleaned),
            "currency": currency_code}  # undefined name: ruff F821
