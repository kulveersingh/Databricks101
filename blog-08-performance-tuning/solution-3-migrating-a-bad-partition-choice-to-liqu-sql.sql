-- Blog 08 — Making Slow Queries Fast: A Databricks Tuning Playbook
-- Exercise 3: Migrating a bad partition choice to Liquid Clustering
-- Requires: Diagnosis is a skill you build by measuring. All three exercises generate their own data and give you before/after numbers you can quote.

-- Date partitioning prunes nothing for a customer_id filter
SELECT COUNT(DISTINCT input_file_name()) AS files_touched
FROM events_partitioned
WHERE customer_id = 12345;

-- Liquid clustering co-locates by customer_id
SELECT COUNT(DISTINCT input_file_name()) AS files_touched
FROM events_clustered
WHERE customer_id = 12345;
-- --- next cell ---

ALTER TABLE events_clustered CLUSTER BY (customer_id, event_date, event_type);
