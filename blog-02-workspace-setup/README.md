# Your First Databricks Workspace: Setup That Doesn't Haunt You Later

Setup takes twenty minutes; workspace *design* is what you're actually doing. This post walks through the ten day-one decisions — account and identity, metastores, environment isolation, naming, and admin guardrails — that determine whether your workspace scales or becomes six months of cleanup, illustrated with a one-afternoon onboarding of a 5-person data team.

![Architecture diagram](./diagram.png)

The diagram shows the account → workspace → catalog hierarchy: a Databricks **account** (billing, users, SSO, audit log delivery) sits above a single Unity Catalog **metastore per region** (the governance plane), which fans out to **one workspace per environment** (`northwind-dev-use1`, `northwind-staging-use1`, `northwind-prod-use1`). Day-one guardrails — cluster policies, personal compute, early audit logs — sit alongside, and catalogs live in the metastore shared across workspaces, with `finance_prod` acting as the security boundary where grants flow downward to schemas and tables.

## Concepts covered

1. **Account, workspace, metastore — three different things.** The account holds billing, users, and metastores. Workspaces are deployments of the UI and compute, tied to a region. The metastore is the governance layer above workspaces. The key insight: workspaces are cheap and disposable; metastores are permanent.
2. **Identity before anything else.** SSO from day one (Okta, Entra ID, Google Workspace), an account-admins group of two or three people documented outside Databricks, and Unity Catalog enabled from the start — the legacy Hive metastore is for backwards compatibility, not new builds.
3. **One metastore per region, assigned deliberately.** Most teams need exactly one metastore per region. Creating a metastore per workspace "for isolation" is actually fragmentation — three governance planes to sync and lineage that stops at workspace boundaries. Give the metastore a boringly-named dedicated storage location.
4. **Isolate with workspaces, not vibes.** One workspace per environment per region — `dev`, `staging`, `prod`, maybe a `sandbox`. Not one per team; that's what catalogs are for. Dev and prod sharing a workspace means enforcing different access rules with discipline, and discipline doesn't survive growth.
5. **Naming conventions: boring is a feature.** `{company}-{env}-{region}` for workspaces, `{domain}_{env}` for catalogs, snake_case everywhere, and never `final`, `v2`, or anyone's name in a permanent object name. Databricks won't enforce this for you — write the ten-line doc and share it.
6. **The five admin settings that matter.** Cluster policies (cost guardrails), workspace access control, a cheap auto-terminating personal compute policy, audit log delivery to your own storage on day one (you can't retroactively generate an audit trail), and IP access lists/PrivateLink before real data lands.
7. **The 5-person team worked example.** SSO-mapped groups, three workspaces on one metastore, a naming doc, per-team cluster policies, audit logs to a locked bucket — four hours of work that absorbed a 3x headcount growth without being touched again.
8. **When this is overkill.** Solo builders exploring one project can use a single workspace; teams with strong platform engineering manage everything as Terraform/Bundles code instead; and regulated multi-region setups need the legal data-residency conversation before the technical one.

## Hands-on exercises

1. **Design the catalog layout for a 3-team retailer.** "Fern & Field" has marketing, finance, and data engineering sharing one workspace, each needing dev/prod separation, with finance PII invisible to marketing. Write the naming doc first, then create six catalogs (`fernfield_{domain}_{dev,prod}`) each with `raw`/`curated`/`gold` schemas, and verify every name against the doc.
2. **Write the cluster policy as code (Premium feature note).** Data-eng keeps spinning up oversized clusters "just to test." Write a cluster policy JSON — ≤8 workers, 30-minute auto-termination, Standard instances only — and peer-review it against the day-one checklist. Note: cluster policies can't be created or applied on Free Edition, so this exercise produces a reviewed artifact, not a live policy.
3. **Audit naming compliance with a query.** Two months in, someone may have created `johns_table` anyway. Query `workspace.information_schema` to flag any schema or table name containing `final`, `v2`, `new`, `test`, or uppercase characters — the same query you'd run the week before an audit.

## Solutions

- `solution-1-catalogs-and-schemas-from-the-naming-doc-doc.md` — The Fern & Field naming doc: workspace, catalog, schema, cluster, and job conventions plus the hard rules (snake_case, no `final/v2/new`, no personal names).
- `solution-1-catalogs-and-schemas-from-the-naming-doc-sql.sql` — SQL that creates the six `fernfield_{domain}_{env}` catalogs with their `raw`/`curated`/`gold` schemas.
- `solution-2-cluster-policy-json-review-artifact.json` — The data-eng cluster policy JSON (8-worker cap, 30-minute auto-termination, Standard instance allowlist), ready to paste into the admin console.
- `solution-3-the-compliance-audit-query.sql` — Information-schema query that lists schemas and tables violating the naming convention.

## Prerequisites

**Databricks Free Edition.** Unity Catalog (catalogs, schemas, grants to `account users`) works on Free Edition. Anything requiring the account console or cluster admin UI is marked — notably exercise 2's cluster policy, which is a Premium feature, so that exercise produces the artifact rather than the live policy.
