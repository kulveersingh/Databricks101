# Change Data Capture: Streaming Your Database to the Lakehouse

Blog 09 of the Databricks series. You will learn how to stop dumping your database every night and stream row-level changes from Postgres into Delta instead: how Debezium, Kafka, and Delta Live Tables' `applyChangesInto` fit together, how to land a raw change stream in bronze, and how to maintain a correct, idempotent silver table that handles updates and deletes — including the two hard parts (deletes and schema drift) that bite every CDC pipeline.

![Architecture diagram](./diagram.png)

The diagram traces the full CDC path: the Postgres operational database's write-ahead log (WAL) is tailed by Debezium, which emits change events into durable Kafka topics (one per table). Autoloader streams them exactly-once into `bronze.order_changes` — a raw, append-only change log. `applyChangesInto` (keys = `order_id`, sequence_by = `updated_at`, `apply_as_deletes`) then maintains `silver.orders` as a materialized, idempotent table of upserts and deletes, feeding gold ops aggregates and a live dashboard whose lag is measured in seconds, not 24 hours. The bottom banner flags the hard parts: deletes must be explicit events (test `apply_as_deletes` in staging), and schema drift should be evolved deliberately with the unexpected quarantined.

## Concepts covered

1. **How CDC actually works.** Your database already records every change in its write-ahead log (WAL in Postgres, binlog in MySQL). Debezium tails that log and publishes change events, Kafka carries them durably, and Databricks consumes the stream — so you never query the production database for analytics again, and the DBA stops worrying about full-table dumps.
2. **Landing the change stream.** The first hop into Databricks is Autoloader, which incrementally ingests the change events into a bronze Delta table: raw, append-only, exactly as they arrived, nothing merged yet. It's the insurance policy — if your merge logic has a bug, you rebuild from here.
3. **applyChangesInto: the merge that handles everything.** DLT's `apply_changes` (also `APPLY CHANGES INTO` in SQL) maintains the silver table from the raw stream: `keys` matches events to rows, `sequence_by` decides which version wins when events arrive out of order, `apply_as_deletes` turns tombstone events into real deletions, and `except_column_list` drops CDC metadata. The sequence column makes every event idempotent — reprocess the same batch twice and the table doesn't change.
4. **The two hard parts: deletes and schema drift.** Deletes aren't row removals in the stream — they're events that say "this row was deleted," so you must test `apply_as_deletes` with real deletes in staging, not just inserts and updates. For schema drift, prefer evolving silver deliberately in a PR (great for additive changes, dangerous for renames) or quarantining unexpected columns into `_rescued_data` with an alert.
5. **Monitoring: watch the lag, not just the rows.** The metric that matters above all is end-to-end lag — row-changed-in-Postgres to visible-in-silver — tracked as a first-class SLA, because CDC failures are often silent slowdowns. Also watch the bronze-vs-silver ingestion gap (a growing gap means the merge can't keep up) and sudden `_rescued_data` spikes (the source schema changed).
6. **When CDC is overkill.** If daily freshness is fine, a scheduled merge from a dump is simpler and cheaper than Debezium + Kafka 24/7; a 10,000-row reference table can just be overwritten nightly; and if you can't access the database log, timestamp-based incremental loads (`WHERE updated_at > last_run`) work. Don't build streaming for a batch requirement.

## Hands-on exercises

1. **E-commerce order statuses from the OLTP** — Generate ~2,000 change events (out-of-order updates, duplicate deliveries, cancelled orders deleted upstream) for ShopNest's orders, land them append-only in bronze, `MERGE` into silver with latest-wins-per-key sequencing and delete-on-cancel, and prove idempotency by re-running the merge as a no-op.
2. **Late price corrections** — Build a change stream where a price correction with an *earlier* `updated_at` arrives *after* a newer one, apply the sequenced merge, and prove the final price follows the source timestamp — not arrival order.
3. **Schema drift into a rescued column** — Land two batches where the second adds `loyalty_tier` mid-stream, detect the drift with a column diff, and merge with schema evolution disabled so the unexpected column lands in a `_rescued_data`-style quarantine column you'd wire to an alert.

## Solutions

- `solution-1-e-commerce-order-statuses-from-the-oltp-py.py` — Seeds the synthetic change events (statuses, out-of-order update, duplicate delivery, cancels) into the bronze landing path.
- `solution-1-e-commerce-order-statuses-from-the-oltp-sql.sql` — The sequenced `MERGE` (ROW_NUMBER over `updated_at` = `sequence_by`, delete on tombstone = `apply_as_deletes`) plus the idempotency and cancel checks.
- `solution-2-late-price-corrections.py` — Seeds the late-arrival price-correction events and applies the sequenced merge to prove source-timestamp ordering wins over arrival order.
- `solution-3-schema-drift-into-a-rescued-column-py.py` — Generates the two-schema batches and computes the drift detector column diff.
- `solution-3-schema-drift-into-a-rescued-column-sql.sql` — Merges the drifted batch into silver with evolution disabled, routing `loyalty_tier` into the rescued quarantine column and counting rescued rows per batch.

## Prerequisites

All three exercises generate their own change streams — no Debezium, no Kafka, no database required. **Tier note:** Free Edition has no Debezium/Kafka, and `dlt.apply_changes` needs the DLT runtime. These exercises simulate the change stream as JSON files and implement `apply_changes` semantics with plain Delta `MERGE` — which is, functionally, what `apply_changes` compiles down to. The sequencing, tombstone, and idempotency properties are identical.

> Companion post: `blog-09-change-data-capture.md` in the Databricks blog series.
