# Blog 14 — Observability: Monitoring Pipelines Like Software
# Exercise 3: the error-budget calculation.
# Requires: Databricks Free Edition with synthetic data. Freshness/quality queries also run against real system tables (system.access, system.lakeflow) when available.

import random

rnd = random.Random(99)
days = []
for d in range(90):
    stale = rnd.randint(5, 100)          # normally well under the 120-min SLA
    if d in (41, 72):                   # two injected breach days
        stale = rnd.randint(180, 400)
    days.append(stale)

breaches = sum(1 for s in days if s > 120)
allowed_breaches = 90 * (1 - 0.995)     # 99.5% SLO -> ~0.45 days
budget_remaining = allowed_breaches - breaches
compliance = 1 - breaches / 90

print(f"breaches={breaches} compliance={compliance:.3%} budget_remaining={budget_remaining:.2f} days")
assert compliance > 0.995               # SLO still met...
assert budget_remaining < 0             # ...but the budget is exhausted
# --- next cell ---

assert budget_remaining < 0, "budget exhausted: freeze non-essential changes"
print("verdict: SLO breached -> freeze changes, harden the pipeline")
