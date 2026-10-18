-- Blog 22 — One Lakehouse, Three Clouds: The Multi-Cloud Finale
-- Exercise 1: residency as catalog config.
-- Requires: You can't rehearse three clouds from one Free Edition workspace — and this finale won't pretend otherwise. These exercises simulate the multi-cloud patterns with catalog naming and synthetic storage p

-- US analytics reads US data. Nothing is granted on the EU side — deliberately.
GRANT SELECT ON SCHEMA us_customers.patients TO `us_analytics`;

-- the compliance check the auditors re-run: any EU privilege held by us_analytics?
CREATE SCHEMA IF NOT EXISTS ops;
CREATE OR REPLACE VIEW ops.eu_residency_check AS
SELECT grantee, table_catalog, table_schema, table_name, privilege_type
FROM eu_customers.information_schema.table_privileges
WHERE grantee = 'us_analytics';

SELECT COUNT(*) AS us_analytics_eu_grants FROM ops.eu_residency_check;
-- Expected outcome: 0. If this view ever returns a row, residency is broken.
