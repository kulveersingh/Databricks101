-- Blog 01 — What Is Databricks, Really? The Lakehouse Explained for Builders
-- Exercise 3: one table, two engines
-- Requires: Everything below runs on Databricks Free Edition. All data is generated inside the notebook — nothing to download.

-- Engine 1: SQL (what the BI dashboard would run)
SELECT page, COUNT(*) AS views
FROM workspace.default.ex03_clicks
GROUP BY page ORDER BY page;
-- --- next cell ---

-- Correct a miscategorized batch, then re-run BOTH reads above
MERGE INTO workspace.default.ex03_clicks t
USING (SELECT * FROM workspace.default.ex03_clicks WHERE page = 'cart') s
ON t.event_id = s.event_id
WHEN MATCHED AND t.user_id % 10 = 0 THEN UPDATE SET t.page = 'checkout';
