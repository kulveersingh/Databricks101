-- Blog 03 — Delta Lake Deep Dive: ACID on Object Storage
-- Exercise 1: status upserts with a time-travel audit trail
-- Requires: All three exercises run on Databricks Free Edition with synthetic data generated in the notebook.

-- What did each version say about order 42?
SELECT 'v0' AS version, status, status_ts FROM workspace.default.ex03b_orders VERSION AS OF 0 WHERE order_id = 42
UNION ALL
SELECT 'v1', status, status_ts FROM workspace.default.ex03b_orders VERSION AS OF 1 WHERE order_id = 42
UNION ALL
SELECT 'v2', status, status_ts FROM workspace.default.ex03b_orders VERSION AS OF 2 WHERE order_id = 42;
