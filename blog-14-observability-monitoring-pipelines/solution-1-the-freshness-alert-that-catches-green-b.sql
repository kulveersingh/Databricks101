-- Blog 14 — Observability: Monitoring Pipelines Like Software
-- Exercise 1: the freshness alert that catches green-but-stale.
-- Requires: Databricks Free Edition with synthetic data. Freshness/quality queries also run against real system tables (system.access, system.lakeflow) when available.

-- Synthetic gold table: healthy for 27 days, frozen for the last 3
CREATE OR REPLACE TEMP VIEW gold_daily_revenue AS
SELECT date_add(current_date(), -i) AS event_date,
       CASE WHEN i < 3 THEN date_add(current_date(), -3)   -- frozen: no new events
            ELSE date_add(current_date(), -i) END AS event_time,
       100000 + (i * 137) % 20000 AS revenue
FROM range(0, 30) AS t(i);

-- The freshness SLA check (same shape as the post's query)
SELECT
  MAX(event_time) AS latest_event,
  TIMESTAMPDIFF(MINUTE, MAX(event_time), CURRENT_TIMESTAMP()) AS minutes_stale,
  TIMESTAMPDIFF(MINUTE, MAX(event_time), CURRENT_TIMESTAMP()) > 120 AS alert
FROM gold_daily_revenue;
-- --- next cell ---

CREATE OR REPLACE TEMP VIEW gold_daily_revenue_healthy AS
SELECT date_add(current_date(), -i) AS event_date,
       date_add(current_date(), -i) AS event_time,
       100000 + (i * 137) % 20000 AS revenue
FROM range(0, 30) AS t(i);

SELECT TIMESTAMPDIFF(MINUTE, MAX(event_time), CURRENT_TIMESTAMP()) > 120 AS alert
FROM gold_daily_revenue_healthy;   -- false: data is fresh
