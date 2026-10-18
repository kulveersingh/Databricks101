# CI/CD for Data Pipelines with GitHub Actions

Blog 12 of the Databricks series. You will learn how to bring software discipline to data pipelines without killing exploratory notebooks: a three-stage GitHub Actions pipeline (lint on every push, integration tests on every PR against a real CI deployment, boring deploys on merge), why the fixture dataset is the unsung hero, how to manage secrets with service principals, and why trunk-based development beats GitFlow when the data never stops changing.

![Architecture diagram](./diagram.png)

The diagram lays out the three stages. The top flow runs: GitHub repo (notebooks, `src/`, `bundle.yml`) → pull request (trunk-based, short-lived branch) → GitHub Actions (runner + service principal) → Databricks targets (ci, staging, prod via Asset Bundles). **Stage 1 — Lint & Validate** runs on every push in seconds and blocks the PR on failure: lint code, validate bundle, check SQL syntax, secret hygiene. **Stage 2 — Integration Test on Every PR** deploys the real DLT pipeline to an isolated CI target with a per-PR scratch catalog, runs it against a 50k-row fixture so expectations fire for real, asserts row counts/null checks/quarantines with pytest, then green-checks or blocks the merge and drops the catalog. **Stage 3 — Deploy on Merge** promotes the same artifact through staging (full pipeline run + smoke checks) to prod (boring on purpose: the same command), explicitly skipping GitFlow — long-lived branches rot against ever-changing data.

## Concepts covered

1. **Why data pipelines break CI/CD assumptions.** A pipeline ships *logic plus data dependencies* — tests can pass while production fails because Tuesday's data looks nothing like Monday's; deployments touch running state (a redeployed streaming pipeline might lose its checkpoint); and notebooks are JSON under the hood, which makes diffs ugly and linters unhappy. So: code is reviewed in PRs, data is validated at runtime, deployments are code promotions, not file copies.
2. **The three stages: lint, test, deploy.** Stage 1 (every push, seconds): `ruff` on Python/notebooks, `databricks bundle validate`, SQL syntax checks. Stage 2 (every PR, minutes): deploy the pipeline to an isolated CI target and run it against a small fixture dataset. Stage 3 (on merge): deploy the *same artifact* to staging, run the full pipeline, then promote to prod. The PR itself triggers a real deployment — you're reviewing code that has already run.
3. **A real-world example: PR checks validating a DLT pipeline.** Northwind Retail's order-analytics DLT pipeline gets a per-PR CI run against a 50,000-row fixture in a scratch catalog created fresh per PR. A real catch: an engineer changed a join key and lint passed, but the CI run failed because the gold aggregation went blank for two regions — the fixture exposed the mismatch before merge. The fixture dataset — versioned, small, nasty — is the unsung hero.
4. **Trunk-based vs GitFlow for data.** GitFlow is actively dangerous for data: long-lived `develop`/`release` branches diverge from main while the production tables kept evolving, so you deploy code tested against data that no longer exists. Trunk-based fits because data is continuous, rollbacks are rebuilds from bronze (keep the previous-good commit hours away), and frequent small merges surface schema incompatibilities early. (Exception: short, automated release branches for regulated change-freeze windows.)
5. **Secrets, service principals, and the boring parts.** CI/CD dies on credential management: use a service principal (not a personal access token tied to someone's account) with narrow Unity Catalog grants scoped to the CI catalog, store the secret in GitHub's encrypted secrets, rotate on a schedule — Databricks OAuth for service principals avoids long-lived tokens. And keep a separate CI workspace from dev: CI destroys and recreates targets constantly.
6. **When CI/CD is overkill.** A team of two doing exploratory analytics with no production jobs doesn't need the ceremony — Git versioning (Databricks Repos) plus code review is enough. The moment a pipeline someone's bonus depends on exists, add the checks: start with lint + bundle validate on PRs (an afternoon's work), add integration tests when the first prod incident would have been caught by them.

## Hands-on exercises

1. **The lint gate catches the Friday-afternoon edit** — Scaffold the repo (`src/transforms.py`, `tests/`, `.github/workflows/ci.yml` with lint and integration-test jobs), plant an unused import and an undefined variable, run `ruff check`, fix until green — and note what `py_compile` would *not* have caught.
2. **The nasty fixture dataset** — Generate a 200-row synthetic orders fixture with null totals, duplicate `order_id`s, negative amounts, and late events; write a pure-Python dedupe/quarantine/gold-aggregate transform plus pytest tests; then introduce the join-key bug (dedupe on `order_ref`) and watch the tests fail — the post's CI catch, reproduced on your laptop.
3. **Drift detection** — Write `drift_check.py` comparing desired state (`resources/orders.job.yml`) against a live-state JSON snapshot, introduce drift (changed schedule, removed failure notification), and get exactly the drifted fields reported — making UI hotfixes visible instead of silent.

## Solutions

- `solution-1-the-lint-gate-catches-the-friday-afterno-yaml.yml` — The `.github/workflows/ci.yml` with the `lint` job (`ruff check` + `databricks bundle validate`) and the `integration-test` job skeleton.
- `solution-1-the-lint-gate-catches-the-friday-afterno-py.py` — `src/transforms.py` with the planted Friday-afternoon bugs (unused import `F401`, undefined name `F821`) for the lint gate to catch.
- `solution-1-the-lint-gate-catches-the-friday-afterno-sh.sh` — The local run script: `pip install ruff` then `ruff check src/ tests/`.
- `solution-2-the-nasty-fixture-dataset.py` — The seeded (42) fixture generator with duplicates, nulls, negatives, and late-arriving events, plus the transform and pytest assertions.
- `solution-3-drift-detection-json.json` — The live-state job snapshot (standing in for the deployed job) that the drifted fields are compared against.
- `solution-3-drift-detection-yaml.yml` — The desired-state `resources/orders.job.yml` the checker diffs against live state.
- `solution-3-drift-detection-py.py` — `drift_check.py`: field-level diff between desired and live job definitions, reporting exactly the drifted fields.

## Prerequisites

Everything here runs locally — a repo directory, `ruff`/`pytest`, and YAML files. No workspace needed. **Tier note:** the only step you can't execute without a workspace is the final deploy, and the workflow shows it as the exact command CI would run. Every check that gates the deploy runs on your laptop.

> Companion post: `blog-12-ci-cd-github-actions.md` in the Databricks blog series.
