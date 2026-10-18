-- Blog 15 — FinOps for Databricks: Stop Burning Money on Clusters
-- Exercise 1: the attribution query.
-- Requires: Databricks Free Edition. Same queries run against real billing system tables (system.billing) when enabled.

-- Synthetic billing: 30 days, tagged, fixed seed via deterministic pseudo-random
CREATE OR REPLACE TEMP VIEW billing_usage AS
SELECT
  date_add(current_date(), - (id % 30)) AS usage_date,
  CASE WHEN id % 4 = 0 THEN 'ml' WHEN id % 4 = 1 THEN 'analytics'
       WHEN id % 4 = 2 THEN 'marketing' ELSE 'platform' END AS team,
  CASE WHEN id % 11 = 0 THEN 'dev-playground'              -- the forgotten experiment
       WHEN id % 4 = 0 THEN 'churn-model'
       WHEN id % 4 = 1 THEN 'revenue-pipeline' ELSE 'bi-dashboards' END AS project,
  CASE WHEN id % 3 = 0 THEN 'ALL_PURPOSE' ELSE 'JOBS' END AS sku,
  CASE WHEN id % 11 = 0 THEN NULL ELSE 'cc-100' END AS cost_center,  -- untagged spend
  10 + (id * 7919) % 90 AS dbus
FROM range(0, 20000) AS t(id);

-- Attribution: DBUs by team/project, untagged spend as its own line
SELECT team, project, sku, SUM(dbus) AS total_dbus
FROM billing_usage
GROUP BY team, project, sku
ORDER BY total_dbus DESC
LIMIT 10;

SELECT 'UNTAGGED' AS team, SUM(dbus) AS untagged_dbus
FROM billing_usage
WHERE cost_center IS NULL;
