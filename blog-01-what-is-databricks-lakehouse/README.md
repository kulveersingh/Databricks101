# What Is Databricks, Really? The Lakehouse Explained for Builders

This post cuts through the "unified analytics platform" marketing to show what's actually running when you click "create cluster." You'll learn the lakehouse idea that makes warehouses and lakes unnecessary, the control-plane/data-plane split that keeps your data inside your own cloud account, and the bronze–silver–gold medallion pattern nearly every production pipeline follows — plus when Databricks is the wrong tool.

![Architecture diagram](./diagram.png)

The diagram shows the full lakehouse architecture: a Databricks-managed **control plane** (workspace UI, Unity Catalog, Workflows, Model Serving, Cluster Manager) sitting above a **data plane** that runs in *your* cloud account. Sources (event streams, databases via CDC, files/APIs) ingest into Delta Lake on object storage, flowing through bronze → silver → gold layers; BI dashboards, ML, and GenAI apps all read from the same tables. Ephemeral clusters in your VPC do the processing — storage and compute are fully separated — while Unity Catalog governs everything with one permission model.

## Concepts covered

1. **The lakehouse idea.** A warehouse gives you structure on expensive proprietary storage; a lake gives you cheap open storage with zero guarantees. The lakehouse keeps the cheap storage and adds the warehouse guarantees on top via an open table format — in Databricks' world, Delta Lake: Parquet files plus a transaction log. That log is what turns a pile of files into a real table.
2. **Control plane vs. data plane.** Databricks is two things: a control plane run by Databricks (UI, notebooks, orchestration, governance) and a data plane in *your* cloud account. When you spin up a cluster, those VMs live in your VPC. Your data never leaves your storage — delete your Databricks account and your Delta tables are still in your buckets.
3. **Compute and storage are fully separated.** Clusters are ephemeral: spin up 50 workers for a backfill, terminate them, pay for 40 minutes. The data just sits in object storage, indifferent to which cluster touched it.
4. **Bronze, silver, gold: the medallion pattern.** Bronze is raw ingestion, append-only — your insurance policy. Silver is cleaned, validated, deduplicated — the layer people trust. Gold is business-level aggregates the dashboards and models actually read. You don't go straight to gold because requirements change, and you rebuild gold from silver, not from a deleted CSV.
5. **One copy, many engines.** The ShopLine example shows why: one copy of the data in S3 as Delta tables, BI reading gold, ML reading silver — no exports between systems, no duplicated storage or compute, and "which table is correct?" stops being a meeting topic.
6. **When NOT to use Databricks.** Dashboards on small data that fits in Postgres, sub-100ms operational queries (Databricks is analytical, not transactional), and teams that won't learn Spark. Honest limits, up front.

## Hands-on exercises

1. **Audit a vendor's data drop with the transaction log.** You're a data engineer at an online retailer whose vendor's weekly product-catalog Delta drop silently removed 2,000 SKUs. Use `DESCRIBE HISTORY` and read the `_delta_log` JSON files to identify exactly which version removed them and what operation it was.
2. **Recover a dashboard table from a bad overwrite.** An analyst's `daily_kpis` table got overwritten with unaggregated raw rows by a misconfigured job. Confirm the pre-corruption version with time travel (`VERSION AS OF`), then `RESTORE` and verify the dashboard numbers are back.
3. **Prove "one copy, many engines."** Write one Delta table of synthetic click events, read it with both a SQL cell and a PySpark cell, apply a `MERGE` correction, and show both engines return identical results — one table, two readers, zero duplication.

## Solutions

- `solution-1-reading-the-transaction-log-py.py` — Builds a 5,000-SKU vendor catalog, applies a price update and an SKU-deleting write, then pinpoints the offending write via `DESCRIBE HISTORY` and `_delta_log`.
- `solution-1-reading-the-transaction-log-sql.sql` — SQL version of the transaction-log audit for exercise 1.
- `solution-2-time-travel-recovery-py.py` — Builds a KPI table, simulates the bad overwrite, verifies the good version with time travel, and restores it.
- `solution-2-time-travel-recovery-sql.sql` — SQL version of the time-travel recovery: `VERSION AS OF` check plus `RESTORE`.
- `solution-3-one-table-two-engines-py.py` — Writes one clickstream Delta table, reads it from PySpark, applies a `MERGE` correction, and compares results across engines.
- `solution-3-one-table-two-engines-sql.sql` — The SQL-reader side of the one-table-two-engines comparison.

## Prerequisites

Everything runs on **Databricks Free Edition**. All data is generated inside the notebook — nothing to download.
