# Unity Catalog: One Governance Layer to Rule Them All

This post answers the concrete question that trips up every audit: "who can access what data, and can you prove it?" You'll learn Unity Catalog's hierarchy (metastore → catalog → schema → table), how to express least privilege as version-controlled SQL grants, why service principals beat shared credentials for pipelines, how automatic lineage turns audits from archaeology into exports, and how external locations let you govern data you already have without moving it.

![Architecture diagram](./diagram.png)

The diagram lays out the permission model: principals on the left (`analysts` reading gold, `data-eng` writing raw/curated, `fraud-ml` reading PII and writing features, `svc-etl-prod` as the pipeline service principal) with grants flowing downward through metastore → catalog → schema → table. `finance_prod` is the security boundary while `finance_dev` mirrors the shape with fake data; PII lives in the raw schema with no grant → no access, and analysts read only `daily_revenue` in gold. Governance outputs on the right: external locations (govern `s3://archive` without moving it), automatic lineage captured at the engine level, and audits as `system.information_schema` queries. The footer states the rules: default deny, pipelines authenticate as service principals, grants as version-controlled SQL, quarterly reviews.

## Concepts covered

1. **The hierarchy: metastore → catalog → schema → table.** One metastore per region, one catalog per domain per environment (`finance_prod`, `marketing_dev`), schemas for layers (`raw`, `curated`, `gold`). Catalogs are the security boundary: grant at the catalog or schema level and every table underneath inherits. Tables are managed (Unity Catalog owns the files) or external (your existing buckets, same governance).
2. **Grants: least privilege, expressed in SQL.** Permissions are just SQL — reviewable, version-controlled, auditable. `GRANT SELECT ON SCHEMA finance_prod.gold TO analysts`; the ETL job's service principal is the *only* writer to `raw`. Two principles do the heavy lifting: **default deny** (no grant = no access, full stop) and **service principals for pipelines** (jobs authenticate as themselves, so departures break nothing and the audit trail names the job).
3. **"Who can read the customers table?" becomes a query.** Instead of digging through IAM policies and shared credentials, you query `system.information_schema.table_privileges` and get principal + privilege back. That's the whole audit-season difference.
4. **Lineage: the audit trail writes itself.** Every read and write is recorded automatically — which job read which table, which tables fed which dashboard — captured at the engine level, not by human diligence. "Show me every downstream consumer of the SSN column" becomes an export instead of a month-long project.
5. **External locations: governing data you already have.** Wrap a storage path with a storage credential, then grant `READ FILES` on the location instead of handing out IAM roles. This is the migration path for five years of Parquet in legacy buckets — wrap it, grant it, govern it, no data movement, no dual-write period.
6. **The Ledgerline SOC 2 example.** A payments startup does the Unity Catalog retrofit six weeks before its audit: catalogs by domain/environment, function-mapped groups, external locations replacing hand-rolled IAM policies, audit logs to immutable storage. The access review became a saved query run monthly. The lesson: governance captured automatically beats governance documented manually.
7. **Limits and complements.** Row/column masking needs dynamic views by design; Unity Catalog is not a DLP product (it won't find PII in free-text columns — pair it with classification tooling); cross-organization sharing uses Delta Sharing, not grants.

## Hands-on exercises

1. **Build the least-privilege layout for a payments startup.** "Ledgerline" stores cardholder PII in `curated.customers`. Create `ledgerline_payments_dev`/`ledgerline_payments_prod` catalogs with `raw`/`curated`/`gold` schemas, grant `account users` (standing in for analysts) `SELECT` on `gold` only, then prove default deny by querying `information_schema.table_privileges` for any grant path to the PII table.
2. **Mask PII with a dynamic view.** Ledgerline's support team needs customer names and order history but must never see full emails. Create the customers table, build a dynamic view showing first-letter-masked emails and hiding account numbers entirely, then compare the view (as support analyst) against the base table (as owner).
3. **Write the monthly access-review query.** Audit season: no screenshots, no spreadsheets. Write one saved query over `system.information_schema` that lists every principal with any privilege on the payments catalogs — answering "who can read the customers table?" every month.

## Solutions

- `solution-1-catalogs-schemas-and-least-privilege-gra.sql` — Creates the Ledgerline dev/prod catalogs and schemas, applies the least-privilege grants, and demonstrates the default-deny check.
- `solution-2-dynamic-view-for-pii-masking-py.py` — Builds the synthetic customers table and the masked dynamic view (PySpark).
- `solution-2-dynamic-view-for-pii-masking-sql.sql` — The dynamic view definition plus owner-vs-analyst comparison queries.
- `solution-3-the-access-review-query.sql` — The saved monthly access-review query over `information_schema`.

## Prerequisites

**Databricks Free Edition.** Catalogs, schemas, SQL grants, and dynamic views all work on Free Edition. Grant to the `account users` group — on Free Edition, workspace-local groups can't receive Unity Catalog grants, so `account users` is the working principal. Anything needing the account console (SSO group mapping, service principals) is marked.
