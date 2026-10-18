# FinOps for Databricks: Stop Burning Money on Clusters

Blog 15 of the Databricks series. A $30,000 invoice lands, nobody can prove what changed, and the Slack thread dies because nobody can attribute anything. This post explains DBUs in plain English — where the money actually goes — and gives the practical playbook for cutting the bill: cluster policies as guardrails, budgets with mid-month trajectory alerts, enforced tagging for attribution, and the right-sizing loop that took a fictional retailer from $30k/month to $12k/month with zero impact on SLAs.

![Architecture diagram](./diagram.png)

The diagram is a Cost Attribution Flow in three columns: COMPUTE (DBU sources — all-purpose clusters at the highest rate, job clusters lower, DLT pipelines lowest, serverless at a premium rate with zero idle waste) → METERING & ATTRIBUTION (`system.billing.usage` → enforced tagging → attribution dashboard) → GUARDRAILS & ACTIONS (cluster policies, budgets & alerts, right-sizing loop). Below it, the Northwind case study in four ordered steps: 1. Attribute (found 40% was idle interactive clusters), 2. Kill the idle (~$8k/mo saved), 3. Right-size jobs (~$5k/mo), 4. Audit premiums (~$5k/mo) — the order they actually did it.

## Concepts covered

1. **The bill has two parts.** Cloud infrastructure cost (VMs paid to AWS/Azure/GCP) plus the Databricks DBU cost (Databricks' management fee). The same VM burns different DBUs per hour depending on workload type — an interactive all-purpose cluster costs roughly 2x the same cluster running a scheduled job.
2. **Idle clusters are the silent killer.** An all-purpose cluster sitting idle at 2am still consumes DBUs; auto-termination isn't optional, it's the single highest-ROI setting in the platform. And you can't optimize what you can't attribute — attribution comes first, optimization second.
3. **Cluster policies are guardrails with teeth.** Define what a cluster *can* be: max workers, instance-type allowlists, auto-termination timeout, Photon on/off, spot instances. Make the restrictive default policy the only option for interactive use; teams request exceptions for bigger clusters.
4. **Budgets turn spend into a monitored metric.** Set a monthly budget at 80% of your target with alerts at 50%, 80%, and 100% — the 50% alert is the useful one, because it tells you mid-month that the trajectory is wrong while there's still time to act.
5. **Tagging makes the invoice explainable.** Enforce `cost_center`, `team`, and `project` tags via cluster policy, then join `system.billing.usage` against your taxonomy so "the ML project cost $11k last month" is a query, not a guess. Treat untagged spend as a bug. Start with showback (visibility) before considering chargeback (actual billing).
6. **The $30k → $12k playbook, in order.** Attribute first (tagging + dashboard: 40% was idle interactive clusters), kill the idle (30-min auto-terminate by policy, delete the always-on dev cluster), right-size the jobs (autoscaling bounds, spot instances, serverless for short runs), audit premiums (Photon only where it earns its keep, right-size warehouses). FinOps is 80% discipline, 20% tuning.
7. **Serverless vs. classic: honest trade-offs.** Serverless wins for bursty, short-lived workloads (you pay for actual usage, not idle clusters); classic wins for long-running predictable workloads with specific instance needs. The trap: assuming serverless is always cheaper — it's priced at a premium per DBU, so profile real usage from `system.billing.usage` before migrating.

## Hands-on exercises

1. **Turn a mystery invoice into a team-by-team breakdown.** Build a synthetic `system.billing.usage` table (30 days, tagged by team/project/SKU, fixed seed), write the attribution query, and find the top offender — the "forgotten experiment" that should be killed.
2. **Catch the trajectory mid-month, not at the invoice.** Take the synthetic billing table, define monthly budgets per project, compute budget-vs-actual at day 15 with 50/80/100% thresholds, and flag the projects whose trajectory will blow past 100%.
3. **Hunt the idle clusters.** Generate a synthetic cluster-uptime log alongside a synthetic query history, join them to find clusters with high DBU consumption and near-zero queries, and estimate the monthly savings from auto-terminating them.

## Solutions

- `solution-1-the-attribution-query.sql` — Builds the synthetic tagged `system.billing.usage` table (30 days, fixed seed) and runs the attribution query by team/project, with untagged spend surfaced as its own line.
- `solution-2-mid-month-trajectory-alerts.sql` — Computes day-15 budget-vs-actual per project at 50/80/100% thresholds and flags the projects on track to blow past 100%.
- `solution-3-the-idle-cluster-hunt.sql` — Joins a synthetic 14-day cluster-uptime log to query history to find high-DBU, near-zero-query clusters and estimates monthly savings from auto-termination.

## Prerequisites

- All three exercises run on Databricks Free Edition using synthetic tables — no workspace billing access needed.
- To run the same queries against real data, enable the `system.billing` schema on your workspace and use your actual `system.billing.usage` table.
