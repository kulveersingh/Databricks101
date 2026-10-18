-- Blog 14 — Observability: Monitoring Pipelines Like Software
-- Exercise 2: three monitors, one synthetic event log.
-- Requires: Databricks Free Edition with synthetic data. Freshness/quality queries also run against real system tables (system.access, system.lakeflow) when available.

-- Synthetic job-run history with a 10-day incident window (days 20-29: green, zero rows)
CREATE OR REPLACE TEMP VIEW job_run_timeline AS
SELECT
  date_add(current_date(), -d) AS run_date,
  CASE WHEN d % 3 = 0 THEN 'api_ingest' WHEN d % 3 = 1 THEN 'dlt_silver' ELSE 'gold_transform' END AS job_name,
  CASE WHEN d BETWEEN 20 AND 29 THEN 'SUCCESS'           -- incident: runs green...
       WHEN d % 17 = 0 THEN 'FAILED' ELSE 'SUCCESS' END AS result_state,
  CASE WHEN d BETWEEN 20 AND 29 THEN 0                    -- ...but writes nothing
       ELSE 10000 + (d * 977) % 5000 END AS rows_written
FROM range(0, 60) AS t(d);

-- 1. Freshness: any job writing zero rows in the last 24h is stale-by-definition
SELECT run_date, job_name
FROM job_run_timeline
WHERE rows_written = 0 AND run_date >= current_date() - 10;

-- 2. Quality: row count vs trailing 7-day median
SELECT run_date, job_name, rows_written,
       rows_written < 0.6 * AVG(rows_written) OVER (
         PARTITION BY job_name ORDER BY run_date
         ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) AS quality_alert
FROM job_run_timeline
WHERE run_date >= current_date() - 15;

-- 3. Pipeline health: failure rate per job over 60 days
SELECT job_name,
       SUM(CASE WHEN result_state = 'FAILED' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS failure_rate
FROM job_run_timeline
GROUP BY job_name;
