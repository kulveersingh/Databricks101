-- Blog 06 — Structured Streaming in Production: Beyond the Tutorial
-- Exercise 1: watermarked cold-chain aggregates with late quarantine
-- Requires: All three exercises run on Databricks Free Edition. There's no Kafka on Free Edition, so the streams below use the built-in `rate` source and file-based Auto Loader — the watermark, checkpoint, and `f

-- The counts must reconcile: windowed input + quarantine = everything generated
SELECT (SELECT SUM(n) FROM workspace.default.ex06_temp_windows)
     + (SELECT COUNT(*) FROM workspace.default.ex06_temp_quarantine)
       AS accounted_for;
SELECT COUNT(*) AS quarantined, MIN(delay_s) / 60.0 AS min_late_minutes
FROM workspace.default.ex06_temp_quarantine;
