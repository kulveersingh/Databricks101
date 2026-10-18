-- Blog 02 — Your First Databricks Workspace: Setup That Doesn't Haunt You Later
-- Exercise 1: catalogs and schemas from the naming doc
-- Requires: Free Edition notes: Unity Catalog (catalogs, schemas, grants to `account users`) works on Free Edition. Anything requiring the account console or cluster admin UI is marked below.

CREATE CATALOG IF NOT EXISTS fernfield_marketing_dev;
CREATE CATALOG IF NOT EXISTS fernfield_marketing_prod;
CREATE CATALOG IF NOT EXISTS fernfield_finance_dev;
CREATE CATALOG IF NOT EXISTS fernfield_finance_prod;
CREATE CATALOG IF NOT EXISTS fernfield_dataeng_dev;
CREATE CATALOG IF NOT EXISTS fernfield_dataeng_prod;
-- --- next cell ---

-- Same three schemas in every catalog: medallion layers with doors on them
CREATE SCHEMA IF NOT EXISTS fernfield_marketing_dev.raw;
CREATE SCHEMA IF NOT EXISTS fernfield_marketing_dev.curated;
CREATE SCHEMA IF NOT EXISTS fernfield_marketing_dev.gold;
-- ... repeat for the other five catalogs
-- --- next cell ---

-- Verify against the doc
SHOW CATALOGS LIKE 'fernfield_*';
SHOW SCHEMAS IN fernfield_finance_prod;
