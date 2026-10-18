-- Blog 03 — Delta Lake Deep Dive: ACID on Object Storage
-- Exercise 3: restore after the bad backfill
-- Requires: All three exercises run on Databricks Free Edition with synthetic data generated in the notebook.

-- Confirm the pre-backfill totals are intact in history
SELECT SUM(revenue) AS good_total
FROM workspace.default.ex03b_order_revenue VERSION AS OF 0;
-- (should equal 12000 + 8500 + 15200 = 35700)

-- Rewind: new version, same data as the good version
RESTORE TABLE workspace.default.ex03b_order_revenue TO VERSION AS OF 0;

-- Verify the dashboard is back
SELECT category, revenue FROM workspace.default.ex03b_order_revenue;
DESCRIBE HISTORY workspace.default.ex03b_order_revenue;
