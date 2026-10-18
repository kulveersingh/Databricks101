# Observability: Monitoring Pipelines Like Software

Blog 14 of the Databricks series. An on-call engineer fixed a failed job at 2am, then got asked the next morning why the revenue dashboard showed last Tuesday's numbers — the job had been "succeeding" for six days, writing zero rows. This post shows how to monitor pipelines like software: ask not "is the job green" but "is the data fresh, sane, and complete" — with freshness alerts on gold tables, quality checks via Lakehouse Monitoring, pipeline-health signals from system tables, and written data SLOs with error budgets.

![Architecture diagram](./diagram.png)

The diagram shows the full monitoring architecture: free signal sources on the left (system tables, Lakehouse Monitoring, pipeline events, table queries, cost signals) feeding three signal tiers in the middle — 1. Freshness (build first, highest value), 2. Quality (is the data sane), 3. Pipeline health (least valuable alone). On the right, a response model: page a human for SLO breaches and critical failures, notify the channel for drift a human should see, dashboard the rest — and link every alert to a runbook. A footer panel captures the data SLOs: freshness, completeness, correctness, reviewed monthly.

## Concepts covered

1. **"Is the data right, fresh, and complete?" — not "is the job green?"** A green checkmark on a job run answers none of those. Most data incidents are staleness incidents wearing a disguise: jobs succeeding on empty inputs while the gold table freezes.
2. **The three signals, in build order.** Freshness first: a dead-simple SQL alert on `MAX(event_time)` per critical table ("gold.orders never more than 2h stale"). Quality second: row-count bounds, null rates, distribution drift. Pipeline health last: job run status and DLT update health — the layer teams monitor first, and the least valuable alone.
3. **System tables: your free observability stack.** Queryable Delta tables in the `system` catalog, populated automatically, with no agents to install: `system.query.history` (slow/expensive queries), `system.billing.usage` (DBU consumption), `system.lakeflow` (DLT pipeline events and expectation violations), `system.access.audit` (who touched what data).
4. **The stale-gold war story.** Northwind's API vendor rotated credentials silently; ingestion kept writing empty batches and everything downstream ran green. Their rebuild order: week 1 freshness alerts on gold tables, week 2 Lakehouse Monitoring profiling, week 3 a platform-team dashboard over `system.lakeflow`, week 4 runbook linkage. Mean-time-to-detect went from days to under 30 minutes.
5. **Write down data SLOs.** Freshness ("never more than 2 hours stale, 99.5% of days per quarter"), completeness ("row counts within ±10% of the trailing 7-day median"), correctness ("zero critical expectation violations per week") — measurable, in the same status page as software SLOs, reviewed monthly. Nobody will sign an SLO for a table nobody uses, and that's useful information.
6. **Borrow the error budget.** If the freshness SLO allows ~3.5 stale days per quarter, track the budget explicitly: healthy budget means ship freely and take risks; exhausted budget means freeze changes and harden. Reliability becomes a number, not a vague virtue.
7. **Don't alert on everything.** Alert fatigue kills observability programs. Don't alert on every transient job failure — alert on business impact: stale gold tables, quality violations, SLO breaches. If the correct response to an alert is "wait and see," it's a dashboard metric, not an alert.

## Hands-on exercises

1. **Page on a stale revenue table — before the CEO does.** A fintech's `gold.daily_revenue` freezes after a silent credential rotation while every downstream job runs green on empty batches: build a synthetic gold table whose data stops at a known timestamp, write the freshness SLA query, and prove the alert trips within the SLA window.
2. **Build the observability stack from a synthetic event log.** System tables are empty on a fresh workspace, so practice on controlled data: generate a synthetic job-run timeline and a synthetic quality-metrics table, then answer the three monitoring questions — freshness, quality, pipeline health — in pure SQL.
3. **Define a freshness SLO and track its error budget.** Generate 90 days of synthetic freshness readings for a gold table with injected breaches, compute SLO compliance and the remaining error budget, and decide whether the team is in "ship freely" or "freeze changes" mode.

## Solutions

- `solution-1-the-freshness-alert-that-catches-green-b.sql` — Synthetic gold table (27 healthy days, 3 frozen days) plus the freshness SLA query from the post; proves the alert condition trips within the window while the job looks "green."
- `solution-2-three-monitors-one-synthetic-event-log.sql` — Synthetic job-run timeline and quality-metrics tables answering freshness (zero-row writers), quality (row counts vs 7-day median), and pipeline health (failure rates) in pure SQL.
- `solution-3-the-error-budget-calculation.py` — Generates 90 days of synthetic freshness readings with injected breaches, computes SLO compliance and remaining error budget, and outputs the ship-freely / freeze-changes verdict.

## Prerequisites

- All three exercises run on Databricks Free Edition using synthetic data — no real incidents required.
- Free Edition note: once system schemas are enabled on a real workspace, query `system.lakeflow.job_run_timeline` and `system.query.history` with the same SQL shape as the exercises.
