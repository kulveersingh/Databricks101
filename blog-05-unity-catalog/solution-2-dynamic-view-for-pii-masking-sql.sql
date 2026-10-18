-- Blog 05 — Unity Catalog: One Governance Layer to Rule Them All
-- Exercise 2: dynamic view for PII masking
-- Requires: Free Edition notes: catalogs, schemas, SQL grants, and dynamic views all work on Free Edition. Grant to the `account users` group below — on Free Edition, workspace-local groups can't receive Unity Ca

-- Support analysts see names and masked emails; account numbers vanish
CREATE OR REPLACE VIEW ledgerline_payments_prod.gold.customers_support AS
SELECT customer_id,
       full_name,
       CONCAT(SUBSTRING(email, 1, 1), '***@',
              SUBSTRING(email, POSITION('@' IN email) + 1)) AS email_masked
FROM ledgerline_payments_prod.curated.customers;
-- --- next cell ---

-- What the support analyst sees (they have SELECT on gold only)
SELECT * FROM ledgerline_payments_prod.gold.customers_support LIMIT 5;

-- What the owner sees (full PII — requires a grant on curated)
SELECT customer_id, full_name, email FROM ledgerline_payments_prod.curated.customers LIMIT 5;
