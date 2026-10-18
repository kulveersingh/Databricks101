-- Blog 04 — Your First ETL Pipeline: CSV to Gold in 30 Minutes
-- Exercise 2: quarantine with the offending file attached
-- Requires: All three exercises run on Databricks Free Edition. Auto Loader (`cloudFiles`) is available on Free Edition — the source directory will be a Unity Catalog Volume, and all CSVs are generated in-noteboo

-- Name the offending file and count its sins
SELECT source_file,
       COUNT(*) AS bad_rows,
       SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS null_ids,
       SUM(CASE WHEN amount < 0 THEN 1 ELSE 0 END) AS negative_amounts
FROM workspace.default.ex04_quarantine
GROUP BY source_file;
