# Delta Lake Deep Dive: ACID on Object Storage

Object storage is a terrible database — no transactions, no schema enforcement — yet every modern data platform stores tables there. This post shows the piece that makes it work: Delta Lake's transaction log. You'll learn what's actually inside a Delta table, how `add`/`remove` log actions give you optimistic concurrency and free time travel, the difference between schema enforcement and deliberate evolution, and how to recover a corrupted table with `RESTORE`.

![Architecture diagram](./diagram.png)

The diagram traces the write path on the left: new or changed rows become immutable Parquet files, and an atomic commit appends a new `_delta_log` JSON entry (the loser of a write race retries). The center shows a `/sales/` table directory with sequential log entries (`add`/`remove` file actions) alongside the data files, noting that removed files linger until VACUUM (7 days) while log history is retained 30 days. On the right, time travel: `VERSION AS OF 40` replays the log up to v40 to recover the pre-corruption state — no backup restore needed. The footer captures the rules: bad writes rejected by default, evolution explicit via `mergeSchema`, and `RESTORE` rewinds through a new log entry so history stays intact.

## Concepts covered

1. **What a Delta table really is.** Embarrassingly simple: Parquet files holding the data plus a `_delta_log` directory of sequentially-numbered JSON files recording which files belong to the table at each version. A Delta "table" is just the log's current opinion about a set of files.
2. **The transaction log, concretely.** Each entry is a list of actions — `add` (this file is now part of the table, with row counts and min/max stats) and `remove` (the file is no longer part of the table; VACUUM deletes it later). A write lands new Parquet files, then atomically appends one JSON entry; racing writers resolve through optimistic concurrency — only one wins, the loser retries.
3. **Time travel is free.** Because every version survives as a separate log entry, `VERSION AS OF` (or `TIMESTAMP AS OF`) just replays the log up to entry N. Nothing is reconstructed; the old file list is simply still there.
4. **Schema enforcement vs. schema evolution.** Enforcement (the default) rejects writes whose columns don't match — the guardrail that stops a broken upstream job from poisoning your table at 3 AM. Evolution (opt-in per write via `mergeSchema`) lets you deliberately add columns or widen types. Rule: enforcement is the default posture, evolution is a conscious decision.
5. **Recovering a corrupted table.** The BrightCart story: a backfill with a cents-instead-of-dollars bug corrupts the gold sales table, and the team `RESTORE`s to the pre-corruption version in under half an hour. `RESTORE` writes a *new* log entry matching the old file list, so the audit trail of what happened stays intact.
6. **Liquid Clustering vs. partitioning.** Stop partitioning everything: over-partitioning creates thousands of tiny files and a file-listing tax on every query. Liquid Clustering declares clustering keys and co-locates related data within files without directories — and you can change keys later without rewriting the table. Reach for physical partitioning only for a clear, single, low-cardinality access pattern.
7. **When Delta Lake isn't the answer.** Sub-second operational reads, workloads that are 90% single-row upserts, and teams that won't run `OPTIMIZE` and `VACUUM` — Delta without maintenance slowly becomes the swamp it was supposed to replace.

## Hands-on exercises

1. **Upsert order statuses, then audit a disputed delivery.** "Mesa Goods" updates order statuses (placed → shipped → delivered) twice daily. A customer files ticket #48210 disputing a delivery date. Build the orders Delta table, apply two `MERGE` upserts, and use time travel to reconstruct that order's exact version-by-version status timeline.
2. **Let schema enforcement save you from a vendor, then evolve deliberately.** Mesa Goods' supplier feed arrives with a surprise fifth column, `discount_code`. Watch schema enforcement reject the unapproved write, then — after confirming it's legitimate — re-run with `mergeSchema` and verify the table gains the column while old rows show null.
3. **Survive a bad backfill.** Finance backfills the `order_revenue` gold table with amounts in cents instead of dollars; the dashboard shows 100x numbers. Confirm the pre-backfill totals with `VERSION AS OF`, then `RESTORE` — and show `DESCRIBE HISTORY` still records the bad write for the postmortem.

## Solutions

- `solution-1-status-upserts-with-a-time-travel-audit-py.py` — Builds 1,000 synthetic orders, applies two `MERGE` status upserts, and reconstructs one disputed order's status history across versions.
- `solution-1-status-upserts-with-a-time-travel-audit-sql.sql` — SQL version of the time-travel audit: per-version status queries for the disputed order.
- `solution-2-enforcement-first-evolution-on-purpose.py` — Demonstrates schema enforcement rejecting the extra-column write, then the deliberate `mergeSchema` evolution.
- `solution-3-restore-after-the-bad-backfill-py.py` — Simulates the cents-not-dollars backfill and restores the revenue table to the good version.
- `solution-3-restore-after-the-bad-backfill-sql.sql` — SQL checks: pre-backfill totals via `VERSION AS OF` plus the `RESTORE` statement.

## Prerequisites

All three exercises run on **Databricks Free Edition** with synthetic data generated in the notebook — no downloads, no external services.
