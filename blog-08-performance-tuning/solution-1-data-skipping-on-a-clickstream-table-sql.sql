-- Blog 08 — Making Slow Queries Fast: A Databricks Tuning Playbook
-- Exercise 1: Data skipping on a clickstream table
-- Requires: Diagnosis is a skill you build by measuring. All three exercises generate their own data and give you before/after numbers you can quote.

-- How many files does the dashboard query actually touch?
SELECT COUNT(DISTINCT input_file_name()) AS files_touched
FROM clickstream
WHERE event_date >= current_date() - 7 AND country = 'CA';

-- The dashboard query itself
SELECT country, AVG(dwell_seconds) AS avg_dwell, COUNT(*) AS events
FROM clickstream
WHERE event_date >= current_date() - 7
GROUP BY country;
-- --- next cell ---

OPTIMIZE clickstream ZORDER BY (event_date, country);

-- Re-run the files_touched probe and DESCRIBE DETAIL numFiles
SELECT COUNT(DISTINCT input_file_name()) AS files_touched
FROM clickstream
WHERE event_date >= current_date() - 7 AND country = 'CA';
