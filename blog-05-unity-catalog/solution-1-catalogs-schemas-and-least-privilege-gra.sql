-- Blog 05 — Unity Catalog: One Governance Layer to Rule Them All
-- Exercise 1: catalogs, schemas, and least-privilege grants
-- Requires: Free Edition notes: catalogs, schemas, SQL grants, and dynamic views all work on Free Edition. Grant to the `account users` group below — on Free Edition, workspace-local groups can't receive Unity Ca

CREATE CATALOG IF NOT EXISTS ledgerline_payments_dev;
CREATE CATALOG IF NOT EXISTS ledgerline_payments_prod;

CREATE SCHEMA IF NOT EXISTS ledgerline_payments_prod.raw;
CREATE SCHEMA IF NOT EXISTS ledgerline_payments_prod.curated;
CREATE SCHEMA IF NOT EXISTS ledgerline_payments_prod.gold;
CREATE SCHEMA IF NOT EXISTS ledgerline_payments_dev.raw;
CREATE SCHEMA IF NOT EXISTS ledgerline_payments_dev.curated;
CREATE SCHEMA IF NOT EXISTS ledgerline_payments_dev.gold;

-- A PII table to protect
CREATE TABLE IF NOT EXISTS ledgerline_payments_prod.curated.customers (
  customer_id STRING, full_name STRING, email STRING, account_no STRING
);
CREATE TABLE IF NOT EXISTS ledgerline_payments_prod.gold.daily_volumes (
  day STRING, txns BIGINT, volume DECIMAL(18,2)
);
-- --- next cell ---

-- Analysts (via `account users` on Free Edition): discover everything, read only gold
GRANT BROWSE ON CATALOG ledgerline_payments_prod TO `account users`;
GRANT USE SCHEMA ON SCHEMA ledgerline_payments_prod.gold TO `account users`;
GRANT SELECT ON SCHEMA ledgerline_payments_prod.gold TO `account users`;
-- Deliberately NO grant on curated: default deny does the rest
-- --- next cell ---

-- Prove it: every privilege any principal holds in the prod catalog
SELECT principal, privilege_type, object_type, object_name
FROM system.information_schema.table_privileges
WHERE table_catalog = 'ledgerline_payments_prod'
ORDER BY object_name, principal;
