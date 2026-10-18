# One Lakehouse, Three Clouds: The Multi-Cloud Finale

Prod on AWS, DR on Azure, analytics on GCP — one Unity Catalog, one governance model, no data fiefdoms. In this finale you'll learn the three multi-cloud topologies (active-passive DR, active-active by workload, residency-first), how to replicate both data *and* catalog metadata across clouds, the failover runbook order (storage → catalog → compute → traffic), and the two operational gotchas that bite real deployments: encoding data residency as catalog config, and the egress bill nobody budgets for.

![Architecture diagram](./diagram.png)

The diagram shows the topology: Unity Catalog spans all clouds as one governance layer (shared schemas, grants, lineage, audit — with per-jurisdiction catalogs for residency). Below it, AWS us-east-1 runs production (S3 Delta tables, DLT pipelines, ML, BI, serving endpoints) and replicates silver + gold to Azure East US, where ADLS holds the replica, catalog metadata syncs hourly, and clusters are defined as code — a warm standby with a 4-hour RTO and quarterly game days. GCP runs analytics as a sandbox: no copies, reads via Delta Sharing under the same UC grants. The failover runbook reads left to right: verify the replica (check the Delta log version), sync the catalog (schemas, grants, lineage), spin up compute (bundle deploy in the DR workspace), then flip traffic (DNS / connection strings). Best practices: residency as catalog config, keep heavy compute next to the data to avoid egress, and standardize with one set of Asset Bundles deployed to N clouds.

## Concepts covered

1. **Three multi-cloud topologies.** Active-passive DR (prod on AWS, warm replicated copy on Azure); active-active by workload (heavy ETL where data gravity is, serving elsewhere, experimental ML on GCP's TPUs — each with its own workspace, governed together); and residency-first (EU data stays in EU regions, enforced by catalog grants). Most real deployments combine all three.
2. **Why the lakehouse is multi-cloud-friendly.** Storage is open formats (Parquet plus the Delta transaction log) and compute is ephemeral — Delta tables don't care which cloud's object store holds them. Multi-cloud breaks architectures where storage and compute are fused; separation is what makes failover portable.
3. **Unity Catalog as the unifying layer.** It governs data across clouds: shared schemas, grants, and lineage everywhere, plus per-jurisdiction catalogs (e.g., `eu_customers`, `us_customers`) for residency. Compute is per-cloud, storage is open, governance is centralized.
4. **Replication has two halves — and teams forget the second.** Data replication (Delta tables copy cleanly; Delta Sharing for governed live reads without copies; real copies for DR since a failover you can't read from isn't a failover) and metadata + governance replication (schemas, grants, lineage must be synced — tables without their catalog are useless).
5. **The failover runbook order.** Storage first (verify the replica is current by checking the Delta log version, not just "files exist"), then catalog, then compute (spin up the DR workspace's clusters from Asset Bundles — a `bundle deploy`, not a snowflake), then flip DNS/connection strings. Write the runbook before 2 AM, not during.
6. **Game-day DR or it isn't DR.** Test failover quarterly: fail a non-critical workload to the DR cloud, run the full suite against the replica, compare row counts and key metrics, fail back. MediCore's first drill found a replication job silently dead for two weeks — that's the point. An untested DR plan is a document, not a capability.
7. **Residency is a catalog problem, not a hope.** Encode it in Unity Catalog: separate catalogs per jurisdiction, grants that prevent cross-border movement, and audit logs proving compliance. "We have a policy" convinces no auditor; "here's the grant configuration and the access logs" does.
8. **Egress costs will surprise you.** Moving data *between* clouds costs real money per GB. Keep heavy compute next to the data (data gravity wins), prefer Delta Sharing over bulk copies where freshness allows, and put every cross-cloud flow behind a cost alert from day one. One set of Asset Bundles, one CI/CD pipeline, one naming convention — deployed to N clouds, or the environments drift into strangers.

## Hands-on exercises

You can't rehearse three clouds from one Free Edition workspace — and this finale doesn't pretend otherwise. These exercises simulate the multi-cloud patterns with catalog naming and synthetic storage paths, all inside one workspace. Each one marks exactly where the simulation ends and real clouds begin.

1. **Make residency a query, not a policy doc.** Create `eu_customers` and `us_customers` catalogs with synthetic patient tables, grant the `us_analytics` group SELECT on the US schema only — deliberately nothing on the EU side — then write the compliance check as a view over the information schema: every privilege on EU objects held by `us_analytics`, asserted to return zero rows.
2. **Run the game-day replica check.** Build an `ops.replica_health` table (table name, primary `s3://` path, DR `abfss://` path, both Delta log versions, heartbeat age) with one planted stale replica (DR 40 versions behind, 3-hour-old heartbeat), then write the game-day query flagging any table where the DR log version trails the primary or the heartbeat is older than 60 minutes.
3. **Find the egress leak.** Build a `finops.cross_cloud_flows` table (flow name, source/destination cloud, GB per day) with one chatty GCP-training-reads-AWS flow, one DR replication flow, and one small BI extract; apply a per-GB egress rate to rank flows by monthly cost, name the top offender with its dollar figure, and write the redesign note (move compute to the data, Delta Sharing, or keep the copy — with the tradeoff stated).

## Solutions

- `solution-1-residency-as-catalog-config-py.py` — Creates the `eu_customers` / `us_customers` catalogs and synthetic patient tables in Python.
- `solution-1-residency-as-catalog-config-sql.sql` — Grants `us_analytics` SELECT on the US schema only, builds the `ops.eu_residency_check` view over the information schema, and asserts zero EU grants.
- `solution-2-the-game-day-replica-check-py.py` — Builds the `ops.replica_health` table with the planted stale replica (`gold.claims`, 40 versions behind).
- `solution-2-the-game-day-replica-check-sql.sql` — The game-day query: flags tables where the DR log version trails the primary or the heartbeat exceeds 60 minutes.
- `solution-3-egress-forensics.py` — Builds `finops.cross_cloud_flows`, applies the illustrative $0.09/GB rate, ranks flows by monthly cost, and names the chatty GCP flow (~$2,295/month) as the top offender with the redesign note.

## Prerequisites

- Databricks Free Edition — all patterns are simulated with catalog naming and synthetic storage paths inside a single workspace; no real clouds needed.
- Note: real cross-cloud replication, real Delta Sharing between workspaces, and real failover need real clouds — and the quarterly game day needs a Saturday, not a notebook.
- Familiarity with Unity Catalog (blog 5), Delta Lake (blog 3), and Databricks Asset Bundles (blog 11) for the runbook and standardization concepts.
