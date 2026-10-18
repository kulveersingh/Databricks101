# Making Slow Queries Fast: A Databricks Tuning Playbook

Blog 08 of the Databricks series. You will learn the tuning order that actually works: a 40-minute dashboard query is usually a file problem, not a compute problem. You'll diagnose with the query profile, turn on Photon, fix file layout with clustering, and automate OPTIMIZE and VACUUM on a cadence — instead of buying bigger clusters to read the wrong files faster.

![Architecture diagram](./diagram.png)

The diagram shows the BrightCart case from the post: **before**, a 12-billion-row events table sits in 48,000 small files with no clustering, so a last-30-day filter still reads *all* files (~40 minutes, no data skipping). **After**, three steps transform it: 1) Photon on, 2) `OPTIMIZE ... ZORDER BY (event_date, region)`, 3) Liquid Clustering plus a daily OPTIMIZE job — data skipping then reads only the matching files (~3 minutes, hundreds of files). The bottom banner pins the cadence to tape to your monitor: OPTIMIZE daily on hot gold tables, VACUUM weekly with a compliance-agreed retention window, automated as a Job.

## Concepts covered

1. **Step 0: diagnose before you tune.** Slow queries have different causes and different fixes. Check the query profile first and measure how much data was read vs. how much was needed — the classic pathology is a 1-month filter reading all five years of files, a file-layout problem no cluster size can fix.
2. **The free lunch: Photon.** Databricks' vectorized query engine processes data in native-code batches instead of row-at-a-time JVM execution, routinely delivering 2–4x speedups on SQL-heavy BI workloads with zero code changes. Check it's on before touching anything else (UDF-heavy PySpark benefits less).
3. **Stop reading files you don't need.** Delta stores per-file min/max column values in the transaction log and automatically skips files that can't match your filter. Layout makes it work: Z-ordering co-locates related rows by your most-filtered columns, and Liquid Clustering declares clustering keys that Delta maintains incrementally as data arrives.
4. **The small-files tax: OPTIMIZE and VACUUM.** Streaming writes thousands of tiny files; each is driver overhead. `OPTIMIZE` compacts them (optionally with Z-ordering); `VACUUM` cleans up the replaced file versions afterward. Cadence matters: OPTIMIZE daily on hot gold tables, VACUUM weekly — and never retain less than your time-travel needs, since VACUUM can delete data you wanted.
5. **Partitioning: use it sparingly.** Hive-style partitioning is the most common over-engineering in tuning — every partition is a directory the driver must list, and over-partitioning recreates the small-files problem. Prefer Liquid Clustering for most tables; reach for physical partitioning only for a stable, high-cardinality split (like one partition per tenant), in the hundreds not hundreds of thousands.
6. **Caching: the most misused knob.** The Delta cache on local SSDs helps only when the same intermediate result is read many times (a dimension table in ten dashboard queries). If the query is slow because it reads five years to answer one month, caching stores the wrong answer faster — fix layout first, cache only genuinely hot tables.
7. **The tuning order.** Profile first, Photon on, file layout, OPTIMIZE + VACUUM cadence, cache last. In that order, and you'll stop buying bigger clusters to solve file problems.

## Hands-on exercises

1. **Data skipping on a clickstream table** — Generate ~2M click events in 60 small append batches to recreate the small-files tax, measure files touched with an `input_file_name()` probe, run `OPTIMIZE ... ZORDER BY (event_date, country)`, and compare before/after.
2. **The daily OPTIMIZE job** — Write 50,000 orders in 30 small batches, write the nightly maintenance SQL (`OPTIMIZE` with a `WHERE` filter on recent dates + `ZORDER BY`, then `VACUUM ... RETAIN 168 HOURS`), and verify idempotency and history with `DESCRIBE HISTORY`.
3. **Migrating a bad partition choice to Liquid Clustering** — Write events partitioned by `event_date`, prove a `customer_id`-filtered query prunes nothing, rebuild with `CLUSTER BY (customer_id, event_date)`, and show the probe improvement plus key evolution without a rewrite.

## Solutions

- `solution-1-data-skipping-on-a-clickstream-table-py.py` — Generates the clickstream data in small batches to recreate the streaming small-files tax.
- `solution-1-data-skipping-on-a-clickstream-table-sql.sql` — The `input_file_name()` before/after probe, the dashboard query, and the `OPTIMIZE ... ZORDER BY` that fixes it.
- `solution-2-the-daily-optimize-job-py.py` — Seeds the small-batch silver orders table needing compaction.
- `solution-2-the-daily-optimize-job-sql.sql` — The nightly maintenance job SQL: filtered `OPTIMIZE`, `VACUUM` with a 7-day window, and the idempotency check via `DESCRIBE HISTORY`.
- `solution-3-migrating-a-bad-partition-choice-to-liqu-py.py` — Builds both the date-partitioned and the liquid-clustered versions of the events table for the head-to-head comparison.
- `solution-3-migrating-a-bad-partition-choice-to-liqu-sql.sql` — The probe queries showing the date-partitioned table prunes nothing on a `customer_id` filter while the clustered one does.

## Prerequisites

All three exercises generate their own data and run on Databricks Free Edition — diagnosis is a skill you build by measuring, and every exercise gives you before/after numbers. **Tier notes:** `OPTIMIZE` and `ZORDER` work on any Delta table; Liquid Clustering needs a runtime that supports `CLUSTER BY` (noted in Exercise 3); Predictive Optimization, mentioned in passing, requires Unity Catalog managed tables.

> Companion post: `blog-08-performance-tuning.md` in the Databricks blog series.
