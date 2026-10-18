-- Blog 05 — Unity Catalog: One Governance Layer to Rule Them All
-- Exercise 3: the access-review query
-- Requires: Free Edition notes: catalogs, schemas, SQL grants, and dynamic views all work on Free Edition. Grant to the `account users` group below — on Free Edition, workspace-local groups can't receive Unity Ca

-- "Who can read the customers table?" — the audit-season query, saved and re-runnable
SELECT principal,
       privilege_type,
       table_catalog, table_schema, table_name
FROM system.information_schema.table_privileges
WHERE table_catalog LIKE 'ledgerline\_%'
  AND (table_name = 'customers' OR privilege_type IN ('SELECT', 'MODIFY', 'ALL PRIVILEGES'))
ORDER BY table_schema, table_name, principal;
