-- Blog 15 — FinOps for Databricks: Stop Burning Money on Clusters
-- Exercise 3: the idle-cluster hunt.
-- Requires: Databricks Free Edition. Same queries run against real billing system tables (system.billing) when enabled.

-- Synthetic cluster uptime + query history, 14 days
CREATE OR REPLACE TEMP VIEW cluster_uptime AS
SELECT cluster_id, 14 * 24 AS uptime_hours,
       CASE WHEN cluster_id = 'dev-shared' THEN 22.0 ELSE 4.5 END AS dbus_per_hour
FROM (SELECT explode(array('dev-shared','etl-nightly','bi-wh','ml-train-1','ml-train-2',
        'adhoc-a','adhoc-b','adhoc-c','streaming','backfill','sandbox-1','sandbox-2'))
      AS cluster_id);

CREATE OR REPLACE TEMP VIEW query_log AS
SELECT 'dev-shared' AS cluster_id, 3 AS queries UNION ALL
SELECT 'etl-nightly', 412 UNION ALL SELECT 'bi-wh', 8930 UNION ALL
SELECT 'ml-train-1', 220 UNION ALL SELECT 'ml-train-2', 198 UNION ALL
SELECT 'adhoc-a', 45 UNION ALL SELECT 'adhoc-b', 12 UNION ALL
SELECT 'adhoc-c', 7 UNION ALL SELECT 'streaming', 0 UNION ALL
SELECT 'backfill', 96 UNION ALL SELECT 'sandbox-1', 2 UNION ALL SELECT 'sandbox-2', 1;

SELECT u.cluster_id,
       ROUND(u.uptime_hours * u.dbus_per_hour) AS total_dbus_14d,
       q.queries,
       ROUND(u.uptime_hours * u.dbus_per_hour / NULLIF(q.queries, 0), 1) AS dbus_per_query
FROM cluster_uptime u JOIN query_log q USING (cluster_id)
ORDER BY total_dbus_14d DESC;
