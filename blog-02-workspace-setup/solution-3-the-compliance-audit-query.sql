-- Blog 02 — Your First Databricks Workspace: Setup That Doesn't Haunt You Later
-- Exercise 3: the compliance audit query
-- Requires: Free Edition notes: Unity Catalog (catalogs, schemas, grants to `account users`) works on Free Edition. Anything requiring the account console or cluster admin UI is marked below.

-- Schemas violating the naming convention
SELECT catalog_name, schema_name
FROM workspace.information_schema.schemata
WHERE catalog_name LIKE 'fernfield\_%'
  AND (schema_name RLIKE '.*(final|v2|new|test).*'
       OR schema_name != LOWER(schema_name));
-- --- next cell ---

-- Tables violating the naming convention
SELECT table_catalog, table_schema, table_name
FROM workspace.information_schema.tables
WHERE table_catalog LIKE 'fernfield\_%'
  AND (table_name RLIKE '.*(final|v2|new|test|john).*'
       OR table_name != LOWER(table_name));
