-- Blog 04 — Your First ETL Pipeline: CSV to Gold in 30 Minutes
-- Exercise 1: Auto Loader ingestion with exactly-once re-runs
-- Requires: All three exercises run on Databricks Free Edition. Auto Loader (`cloudFiles`) is available on Free Edition — the source directory will be a Unity Catalog Volume, and all CSVs are generated in-noteboo

CREATE VOLUME IF NOT EXISTS workspace.default.ex04_drop;
