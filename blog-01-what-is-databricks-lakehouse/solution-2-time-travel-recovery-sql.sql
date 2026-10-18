-- Blog 01 — What Is Databricks, Really? The Lakehouse Explained for Builders
-- Exercise 2: time travel recovery
-- Requires: Everything below runs on Databricks Free Edition. All data is generated inside the notebook — nothing to download.

-- Confirm version 0 still has the good numbers
SELECT * FROM workspace.default.ex02_daily_kpis VERSION AS OF 0;

-- Rewind the table: writes a NEW version whose file list matches version 0
RESTORE TABLE workspace.default.ex02_daily_kpis TO VERSION AS OF 0;

-- Verify
SELECT * FROM workspace.default.ex02_daily_kpis;
DESCRIBE HISTORY workspace.default.ex02_daily_kpis;
