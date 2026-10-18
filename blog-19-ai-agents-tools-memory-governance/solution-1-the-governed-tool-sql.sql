-- Blog 19 — AI Agents on Databricks: Tools, Memory, and Governance That Holds Up
-- Exercise 1: the governed tool.
-- Requires: Agents are systems you can rehearse. These three exercises build Northwind's report agent at small scale on Free Edition: Unity Catalog functions work on serverless compute, but the `system.access` au

CREATE OR REPLACE FUNCTION sales.weekly_by_segment(in_region STRING)
RETURNS TABLE (segment STRING, churn_rate DOUBLE, revenue_at_risk DOUBLE)
RETURN
  SELECT segment,
         AVG(churned) AS churn_rate,
         SUM(arr) FILTER (WHERE churned = 1) AS revenue_at_risk
  FROM sales.customer_monthly
  WHERE region = in_region AND quarter = 'Q3'
  GROUP BY segment;

GRANT EXECUTE ON FUNCTION sales.weekly_by_segment TO `analysts`;

-- the verification that matters: who is allowed to wield this tool?
SHOW GRANTS ON FUNCTION sales.weekly_by_segment;
