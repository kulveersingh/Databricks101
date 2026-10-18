# Databricks Asset Bundles: Infrastructure as Code Done Right

Blog 11 of the Databricks series. You will learn how Databricks Asset Bundles turn "deployed by hand, nobody knows which workspace has the current version" into infrastructure as code: package jobs, DLT pipelines, and dashboards in Git with `databricks.yml`, promote one definition through dev, staging, and prod targets with per-target variables, and make rollback a `git revert` plus a redeploy.

![Architecture diagram](./diagram.png)

The diagram shows the full loop: a Git repo (one `databricks.yml` definition plus `src/` and `tests/`) passes through validate into CI (`bundle validate`, lint + unit tests, GitHub Actions), then promotes through `dev` (`deploy -t dev`, per-developer prefixes, fast iteration) → `staging` (merge to main, prod-like data, soak + integration tests) → `prod` (release, clean names, smoke tests). A dashed rollback arrow runs straight from prod back to Git — a bad deploy is undone with a revert and redeploy, a Git SHA, not a project. The bottom banner pins the two safety rules: per-target variables (warehouse IDs, schedules, alert lists — structure identical, values differ), and secrets live in secret scopes, never in the YAML, never in Git.

## Concepts covered

1. **What a bundle actually is.** A directory with a `databricks.yml` describing everything your project needs — notebooks, jobs, DLT pipelines, clusters, dashboards — plus the code itself, all versioned in Git. The `${bundle.target}` templating means one definition deploys to every environment, and `bundle deploy` creates or updates everything while cleaning up resources removed from the definition.
2. **One bundle, three targets.** The `targets` block ends environment folklore: development mode prefixes resource names and isolates them per developer (two engineers can't clobber each other), production mode deploys clean names. If it's not in the bundle, it's not in the environment — the "oops" class of hand-built discrepancies dies.
3. **Laptop → prod promotion.** Priya's returns pipeline flows from a feature branch (code, deploy to dev, test in minutes) → PR (CI runs `bundle validate` plus integration tests against staging data) → staging (merge to main, scheduled soak against prod-like data, watch the DLT expectations dashboard) → prod (release branch or manual gate deploys the exact artifact that ran clean in staging). Auditors get a Git SHA instead of a shrug.
4. **The full CI/CD loop.** Bundles are the deployment half; CI is the automation half — on PR: `bundle validate`, lint, unit tests; on merge to main: deploy to staging and run integration tests; on release: deploy to prod with smoke tests and a Slack notify. For data pipelines, trunk-based with short-lived feature branches usually beats GitFlow (full treatment in post #12).
5. **Variables: one bundle, many configs.** Bundle variables (`${var.warehouse_id}`) with per-target values replace hardcoding — cluster sizes, schedules, alert email lists, catalogs. Structure stays identical; only values change. When someone asks "what's different about prod?", the answer is a short variable list, not a diff of two hand-built workspaces.
6. **Honest limits.** Bundles are for production artifacts, not ad-hoc exploration — nobody should bundle-ify a notebook they're still thinking in. The YAML schema has a learning curve (it pays back on the second deploy), and bundles complement Terraform rather than replacing it: bundles own Databricks-internal resources (jobs, pipelines, dashboards), Terraform owns the cloud estate (VPCs, IAM, workspaces).

## Hands-on exercises

1. **Bundle-ify Priya's returns pipeline** — Scaffold a bundle project (`databricks.yml` with dev/staging/prod targets, a nightly returns job, a stub transform), write `check_bundle.py` verifying the YAML parses, referenced notebook paths exist, and every target declares a workspace host — then print the per-target resolved resource names.
2. **Per-target variables** — Add `catalog` and `alert_email` variables with per-target values, reference them from the job definition, extend the checker to resolve variables and fail loudly on undefined references, and print the fully resolved job config per target.
3. **Generate a bundle from a hand-built job** — Write `capture_job.py` that reads a UI-built job's spec JSON and emits `resources/<name>.job.yml` in bundle resource format, then validate the emitted YAML — the migration path from click-ops to Git.

## Solutions

- `solution-1-bundle-ify-priya-s-returns-pipeline-yaml.yml` — The `databricks.yml` with the `returns_pipeline` bundle name and dev/staging/prod targets.
- `solution-1-bundle-ify-priya-s-returns-pipeline-py.py` — The stub returns pipeline transform plus the local `check_bundle.py`-style structural validation logic.
- `solution-2-per-target-variables-yaml.yml` — The `variables` block (`catalog`, `alert_email`) with per-target values referenced from the job definition.
- `solution-2-per-target-variables-py.py` — The variable-resolution checker that fails loudly on undefined variable references.
- `solution-3-generate-a-bundle-from-a-hand-built-job-py.py` — `capture_job.py`: reads the sample hand-built job JSON and emits bundle-format `resources/<name>.job.yml`.
- `solution-3-generate-a-bundle-from-a-hand-built-job-sh.sh` — The one-line runner that validates the emitted bundle with the local checker.

## Prerequisites

All three exercises run locally — a project directory, YAML files, and a Python checker. No workspace needed. **Tier note:** `databricks bundle validate` and `bundle deploy` need the Databricks CLI authenticated to a workspace, which a bare checkout doesn't have. These exercises build a real bundle project and validate it with a local checker that enforces the same structural rules — the YAML you write here deploys unchanged once you point the CLI at a workspace.

> Companion post: `blog-11-databricks-asset-bundles.md` in the Databricks blog series.
