-- Blog 04 — Your First ETL Pipeline: CSV to Gold in 30 Minutes
-- Exercise 3: redefine revenue, rebuild, diff the re-run
-- Requires: All three exercises run on Databricks Free Edition. Auto Loader (`cloudFiles`) is available on Free Edition — the source directory will be a Unity Catalog Volume, and all CSVs are generated in-noteboo

-- Gold: finance's new definition — refunded orders don't count
CREATE OR REPLACE TABLE workspace.default.ex04_gold_daily_revenue AS
SELECT SUBSTRING(order_ts, 1, 8) AS order_day,
       SUBSTRING(order_id, 1, 2) AS drop_day,
       COUNT(*) AS orders,
       SUM(CASE WHEN NOT is_refunded THEN amount ELSE 0 END) AS revenue
FROM workspace.default.ex04_silver_orders
GROUP BY 1, 2;
-- --- next cell ---

-- Snapshot, re-run everything, diff: idempotency proof
CREATE OR REPLACE TEMP VIEW gold_run1 AS SELECT * FROM workspace.default.ex04_gold_daily_revenue;
-- --- next cell ---

-- Both directions must return zero rows
(SELECT * FROM workspace.default.ex04_gold_daily_revenue
 EXCEPT
 SELECT * FROM gold_run1)
UNION ALL
(SELECT * FROM gold_run1
 EXCEPT
 SELECT * FROM workspace.default.ex04_gold_daily_revenue);
