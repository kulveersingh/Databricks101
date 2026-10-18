# Your First ETL Pipeline: CSV to Gold in 30 Minutes

From a messy folder of daily CSVs to trusted gold tables: this post builds the medallion pipeline pattern in working code. You'll learn Auto Loader (`cloudFiles`) for exactly-once incremental ingestion, a silver layer that validates, quarantines, and deduplicates instead of silently dropping rows, a deliberately boring gold layer, and the core principle tying it together — design every layer to be re-runnable so failures become "it retried" instead of "I spent Tuesday unpicking duplicates."

![Architecture diagram](./diagram.png)

The diagram shows the full medallion flow: daily CSV drops land in the source folder, Auto Loader (`cloudFiles` with checkpoints) ingests them incrementally and exactly-once into append-only **bronze** (`orders_raw`, raw as-arrived plus the source file), which feeds **silver** (validate → dedup → `MERGE`, one row per order, enforced schema) with rejects routed to a visible **quarantine** table (bad rows + source file, never silently dropped), and finally **gold** (`daily_revenue` business aggregates) that BI reads from the `shop_prod` catalog. Every stage is marked re-runnable; the footer summarizes the layers as insurance, trust, and speed, with dev → prod promotion as a conscious step.

## Concepts covered

1. **The shape of the pipeline: medallion in practice.** Bronze lands raw CSVs exactly as they arrived, append-only. Silver parses, validates, deduplicates, and fixes types. Gold holds business-ready aggregates the dashboard reads. Data flows one direction and each layer has one job.
2. **Bronze: Auto Loader, the ingestion workhorse.** The naive `spark.read.csv("*.csv")` re-reads everything every run and double-loads on re-runs. Auto Loader watches the source directory incrementally — new files processed exactly once, tracked via checkpoints. `schemaLocation` pins the schema so a surprise column gets flagged, `_metadata.file_path` records which file each row came from, and `trigger(availableNow=True)` turns the stream into a process-and-stop batch for a daily feed.
3. **Silver: clean it like you don't trust it.** Parse strings into real types (bad rows become null, not exceptions), validate and route rejects to a quarantine table *with the source file attached* — "we dropped 0.3% of rows" is a reportable fact, silently dropping them is a future incident. Deduplicate by `order_id` keeping the latest file's version, then `MERGE` into silver for an idempotent upsert.
4. **Gold: the table the business actually reads.** Deliberately boring — small, fast, purpose-built aggregates. Notice the catalog separation: bronze/silver were built in `shop_dev`, but gold lives in `shop_prod`. Promoting to prod is a conscious step, not an accident.
5. **Idempotency at every layer, not just ingestion.** Auto Loader handles bronze, `MERGE` handles silver, `CREATE OR REPLACE` handles gold. Test the re-run before you need it: run the whole pipeline twice on a calm Tuesday and diff the outputs — if the second run changes anything, your idempotency has a hole. Also: partition bronze by ingest date, keep the original CSVs as last-resort evidence, and version notebooks in Git.
6. **The ParcelPost example.** Rebuilding a retailer's cron-job pipeline made duplicates impossible by construction (checkpoints + `MERGE`), turned schema drift into a visible, quarantined event, and let finance redefine "revenue" by rebuilding gold from silver in one query. The team's verdict: "the pipeline stopped being something we think about."
7. **When not to build it this way.** One-off analysis (just read the CSV into a notebook), sub-minute freshness needs (that's streaming, post #6), and sources that are already databases (CDC straight into Delta beats file drops).

## Hands-on exercises

1. **Ingest the daily SFTP drop — then prove re-runs are boring.** ParcelPost drops one `orders_*.csv` per day into a folder; a duplicate file once inflated a Black Friday report. Generate three synthetic daily CSVs in a Volume, ingest them with Auto Loader (`cloudFiles`, `trigger(availableNow=True)`) recording `_metadata.file_path`, run the stream a second time, and prove zero new files were processed.
2. **Quarantine the bad rows — and name the file that sent them.** A regional supplier sends a CSV with negative amounts and null order_ids. The pipeline must not crash and must not silently drop rows: invalid rows land in a quarantine table carrying their source file path, and you query it to identify exactly which file broke and why.
3. **The business redefines revenue — rebuild gold without fear.** Finance decides revenue must exclude refunded orders, retroactively. Add an `is_refunded` flag to silver (~5% refunded), rebuild gold as daily revenue by category with `CREATE OR REPLACE`, then run the full pipeline twice and diff with `EXCEPT` — both diffs must return zero rows.

## Solutions

- `solution-1-auto-loader-ingestion-with-exactly-once-py.py` — Generates three daily CSVs in a Volume, ingests them with Auto Loader, and proves the second run processes nothing new.
- `solution-1-auto-loader-ingestion-with-exactly-once-sql.sql` — SQL setup (Volume) and verification queries for the exactly-once ingestion.
- `solution-2-quarantine-with-the-offending-file-attac-py.py` — Silver cleaning step routing invalid rows to a quarantine table tagged with the offending file path.
- `solution-2-quarantine-with-the-offending-file-attac-sql.sql` — SQL query that names the offending file and counts each of its bad rows.
- `solution-3-redefine-revenue-rebuild-diff-the-re-run-py.py` — Flags ~5% of silver orders as refunded and rebuilds gold excluding refunded revenue.
- `solution-3-redefine-revenue-rebuild-diff-the-re-run-sql.sql` — SQL gold table under finance's new revenue definition plus the `EXCEPT` diff proving the re-run changes nothing.

## Prerequisites

All three exercises run on **Databricks Free Edition**. Auto Loader (`cloudFiles`) is available on Free Edition — the source directory is a Unity Catalog Volume, and all CSVs are generated in-notebook.
