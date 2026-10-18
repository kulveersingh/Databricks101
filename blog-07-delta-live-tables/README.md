# Delta Live Tables: Declarative Pipelines That Fix Themselves

Blog 07 of the Databricks series. You will learn how Delta Live Tables (DLT) replaces hand-written, imperative pipeline scripts with a declarative model: you declare your bronze, silver, and gold datasets plus data-quality expectations, and DLT figures out execution order, retries, checkpointing, and recovery — so schema drift and bad rows stop turning into 2:47 AM pages.

![Architecture diagram](./diagram.png)

The diagram walks through a marketing-attribution pipeline built the DLT way. Ad-platform exports (Meta, Google, TikTok) and an orders CDC stream land via Autoloader into `bronze_touchpoints` (raw, append-only). `silver_touchpoints` applies the quality gates — `expect_or_drop` on timestamps and campaign IDs, `expect_or_fail` on non-negative spend — with offending rows quarantined (kept in bronze, never lost). Clean data flows into an incremental `gold_attribution` table that feeds the ROAS dashboard. The bottom banner summarizes the pipeline settings (dev vs production mode, autoscaling + Photon, continuous vs triggered) and the two repair options (full refresh vs surgical pipeline repair).

## Concepts covered

1. **The old way: imperative pipelines that rot.** A traditional pipeline is a script that says *how* — read this file, join, dedupe, merge. It works on day one, then schema drift, source outages, or duplicate batches arrive and the script — which has no idea what "correct" means — happily writes garbage into gold tables, leaving you babysitting it.
2. **The DLT way: declare what, not how.** You declare datasets and transformations with `@dlt.table` in Python or SQL, and DLT builds the DAG, runs the streaming reads, handles retries and checkpointing, and keeps tables in sync. Add a new table and the pipeline just absorbs it — no merge statements, no checkpoint paths, no resume logic.
3. **Expectations: data quality as code.** Attach declarative rules directly to tables: `expect` records the metric while keeping the row; `expect_or_drop` quarantines offenders (bad rows stay in bronze); `expect_or_fail` stops the pipeline when something is deeply wrong, like negative spend. Quality lives *inside* the pipeline, not in an after-the-fact report job.
4. **Pipeline settings that actually matter.** Development mode runs once and stops (fast iteration, no retries); production mode runs continuously or on schedule with automatic retries and alerts — develop in dev, deploy in production. DLT manages the cluster (size, autoscaling, Photon); streaming sources run continuously, batch sources on a trigger.
5. **Repairs: when bad data already got through.** No quality gate catches everything, so DLT gives you full refresh (rebuild from scratch — the nuclear option) and pipeline repair (reprocess only the data affected by a failed update, surgically). The pattern: fix the expectation, run a repair, check the metrics dashboard, move on — no hand-rolled backfill scripts.
6. **When DLT isn't the answer.** DLT is a batch/micro-batch engine, so sub-second feature serving needs something else; pipelines needing external API calls, human approvals, or cross-cloud coordination belong in Databricks Workflows or Airflow; and always-on continuous pipelines keep a cluster warm, so daily-freshness data is cheaper as a triggered pipeline or plain Job.
7. **Treat expectations like contracts.** Version expectations alongside the transformation in the same PR; alert on sudden spikes in quarantined rows as an early upstream-change warning; start with `expect` to record metrics, graduate to `expect_or_drop` once you trust the thresholds.

## Hands-on exercises

1. **Quality-gated airline bookings** — Ingest ~5,000 synthetic SkyRoute booking events with planted bad rows into bronze via Autoloader, then gate silver with `@dlt.expect_all_or_drop` on key rules plus `@dlt.expect_or_fail` on non-negative amounts, and verify drops and idempotency in the DLT UI metrics.
2. **Expect vs. expect_or_drop vs. expect_or_fail** — Build three silver tables off one bronze taxi-trip source, each using one expectation behavior, and read the metrics to see exactly how many rows each behavior kept, dropped, or recorded — including the pipeline-stopping fail.
3. **CDC on a product catalog with apply_changes** — Mirror a Postgres-style product catalog (inserts, out-of-order price updates, discontinued products, duplicate deliveries) into silver using `dlt.create_target_streaming_table` + `dlt.apply_changes`, sequenced by `updated_at`, deletes applied on tombstone events.

## Solutions

- `solution-1-quality-gated-airline-bookings.py` — Seeds the SkyRoute booking JSON and defines the bronze/silver DLT pipeline with expectation rules, plus a Free Edition fallback that simulates the same semantics in a plain notebook.
- `solution-2-expect-vs-expect-or-drop-vs-expect-or-fa.py` — Generates trip records with bad rows and builds the three behavior-comparison silver tables so you can see record vs. quarantine vs. stop in one run.
- `solution-3-cdc-on-a-product-catalog-with-apply-chan-py.py` — Seeds out-of-order product change events (inserts, updates, deletes, duplicates) for the `apply_changes` exercise.
- `solution-3-cdc-on-a-product-catalog-with-apply-chan-sql.sql` — The SQL equivalent: seeds bronze and builds the sequenced silver table with delete-on-tombstone semantics.

## Prerequisites

All three exercises generate their own data — no downloads, no external services. **Tier note:** DLT pipelines run on DLT/serverless compute, which sits outside the Free Edition allowance. The exercise code is real DLT code you'd attach to a pipeline, and each solution includes a plain-notebook fallback so you can validate the same logic on Free Edition right now.

> Companion post: `blog-07-delta-live-tables.md` in the Databricks blog series.
