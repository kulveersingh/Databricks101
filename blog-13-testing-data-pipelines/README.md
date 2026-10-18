# Testing Data Pipelines: Unit, Integration, and Data Quality Tests

Blog 13 of the Databricks series. For software, "it works on my machine" is a joke — for data pipelines it's terrifying, because the failure mode isn't a crash, it's silence: the pipeline runs green, the dashboard updates, and the numbers are quietly wrong. This post shows the test pyramid that actually catches bad data: fast pytest unit tests for transform logic, end-to-end integration tests against fixture data, and DLT expectations that act as data-quality contracts running in production.

![Architecture diagram](./diagram.png)

The diagram lays out the Test Pyramid for Data Pipelines: a base of many fast unit tests (pytest on pure transform functions, DataFrame in → DataFrame out, no cluster needed), a middle layer of slower integration tests (deploying the DLT pipeline to a CI target against versioned fixtures), and a top of continuous data-quality tests (expect_or_drop / expect_or_fail running in production on every batch). Alongside it: the fixture-dataset discipline that underpins every layer (versioned, nasty, deterministic, seeded) and "The Northwind Catch" — the real-world example where a silent customer_id int→UUID schema change was caught by expect_or_fail before it poisoned the gold table.

## Concepts covered

1. **Silent failures are the real failure mode.** A pipeline's most dangerous outcome isn't a 3am crash — it's running green while producing wrong numbers. "It ran without errors" is not a test, because nobody is asserting that the data is right.
2. **The data test pyramid.** Base: unit tests — fast, numerous, run on every commit. Middle: integration tests — slower, deploy the real pipeline to an isolated environment and run it end-to-end on fixture data. Top: data quality tests — not run in CI at all, but continuously in production on every batch.
3. **Unit-test transforms with pytest, not notebook cells.** The architectural trick: keep transform logic in importable Python modules, so a function like `clean_orders` can be tested with five hand-written rows in milliseconds using a local Spark session. If your logic is trapped in a notebook cell, you can't unit test it.
4. **Write the regression test first.** When a production incident reveals a transform bug, the first commit is a failing unit test that reproduces it; the second is the fix. Over a year this builds a regression suite shaped like your team's real failure modes — and keep unit tests hermetic: if a test needs a cluster, a real table, or the network, it belongs in the integration layer.
5. **DLT expectations are contracts with your data producers.** `expect_or_drop` quarantines bad rows to an error table you can inspect; `expect_or_fail` kills the pipeline when the data is corrupt. An expectation firing in prod isn't a pipeline bug — it's a signal that the upstream contract broke, with a quarantine table full of evidence.
6. **The schema-change war story.** A checkout vendor silently changed `customer_id` from integer to string UUID with no announcement. The expectation killed the nightly run, the gold table stayed untouched, the quarantine log identified the root cause in minutes, and the fix shipped through CI with a new regression test — versus three weeks of corrupted attribution numbers.
7. **Fixture datasets are the foundation.** Version fixtures with the code, keep them small (thousands of rows) but adversarial (nulls, duplicates, out-of-range values, unicode, DST-boundary timestamps), generate the bulk deterministically with a fixed seed, and refresh from production *shapes*, never production *data*.

## Hands-on exercises

1. **Catch the currency-unit bug before it costs you.** A checkout provider silently switches from dollars to cents and revenue jumps 100x overnight: build a fixed-seed synthetic orders feed, write a `clean_orders` unit test asserting on `amount_cents`, then flip the feed to cents and watch the test fail.
2. **Quarantine a silent schema change instead of dropping data.** A source team changes `customer_id` from integer to string UUID with no announcement: run ingestion against fixture data with both formats, enforce an expectation that quarantines the bad rows, and prove the quarantine table holds the evidence.
3. **Build an adversarial fixture that looks like your worst day.** Write a deterministic fixed-seed fixture generator for an orders feed that injects nulls, duplicate keys, out-of-range amounts, unicode names, and DST-boundary timestamps, then run a null-spike quality check over it.

## Solutions

- `solution-1-the-currency-unit-regression-test.py` — Pytest unit test for `clean_orders` over a fixed-seed synthetic orders feed; reproduces the dollars→cents regression and proves the test catches it.
- `solution-2-quarantine-don-t-silently-drop.py` — Ingestion against a fixture of 950 integer ids, 50 UUID strings, and 2 nulls, with an expectation that quarantines (not silently drops) rows from the silent customer_id type change.
- `solution-3-deterministic-adversarial-fixtures.py` — Fixed-seed deterministic fixture generator injecting nulls, duplicate keys, out-of-range amounts, unicode, and DST-boundary timestamps, plus a null-spike quality check over the output.

## Prerequisites

- Exercises 1 and 3 run locally in pure Python/pytest with a local Spark session — no workspace, no cluster, no cloud bill.
- Exercise 2 uses DLT expectations against a real pipeline deploy, so it needs a Databricks workspace with Delta Live Tables (a Premium-tier feature); adapt to `dlt` on your own pipeline target.
