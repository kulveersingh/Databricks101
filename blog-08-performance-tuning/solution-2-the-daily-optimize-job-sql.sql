-- Blog 08 — Making Slow Queries Fast: A Databricks Tuning Playbook
-- Exercise 2: The daily OPTIMIZE job
-- Requires: Diagnosis is a skill you build by measuring. All three exercises generate their own data and give you before/after numbers you can quote.

-- Compact only recent data (the hot part), co-located for dashboard filters
OPTIMIZE silver_orders
WHERE order_date >= current_date() - 30
ZORDER BY (order_date, store_id);

-- Clean up replaced files, keeping a 7-day time-travel window
VACUUM silver_orders RETAIN 168 HOURS;
-- --- next cell ---

-- Run the OPTIMIZE again: it should be a fast no-op
OPTIMIZE silver_orders
WHERE order_date >= current_date() - 30
ZORDER BY (order_date, store_id);

DESCRIBE HISTORY silver_orders;
