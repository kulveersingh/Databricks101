-- Blog 15 — FinOps for Databricks: Stop Burning Money on Clusters
-- Exercise 2: mid-month trajectory alerts.
-- Requires: Databricks Free Edition. Same queries run against real billing system tables (system.billing) when enabled.

WITH budgets AS (
  SELECT 'churn-model' AS project, 220000 AS monthly_budget UNION ALL
  SELECT 'revenue-pipeline', 200000 UNION ALL
  SELECT 'bi-dashboards', 500000 UNION ALL
  SELECT 'dev-playground', 0          -- no budget: any spend is an alert
),
actuals AS (
  SELECT project, SUM(dbus) AS dbus_15d
  FROM billing_usage
  WHERE usage_date >= current_date() - 15
  GROUP BY project
)
SELECT a.project, b.monthly_budget, a.dbus_15d,
       a.dbus_15d * 2 AS projected_month,
       CASE WHEN b.monthly_budget = 0 AND a.dbus_15d > 0 THEN 'OVER: unbudgeted'
            WHEN a.dbus_15d * 2 > b.monthly_budget THEN 'OVER: projected breach'
            WHEN a.dbus_15d * 2 > 0.8 * b.monthly_budget THEN 'WARN: 80% trajectory'
            ELSE 'OK' END AS status
FROM actuals a JOIN budgets b USING (project)
ORDER BY projected_month DESC;
