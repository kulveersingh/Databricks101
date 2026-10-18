# Databricks NOC Dashboards — Terraform Automation

Companion infrastructure for **Chapter 19 ("The NOC Dashboard")** of *Databricks Internals*.
This package creates, via
Terraform, the Dynatrace and Datadog dashboards, P1–P5 alerting, and Databricks webhook wiring
that put Databricks pipeline run status (running / failed / success) on the NOC's screens.

## Architecture

```
Databricks                              Observability platforms                  NOC
─────────                              ───────────────────────                  ───
Lakeflow Jobs
  ├─ job webhooks (on_start /        ┌─ Dynatrace ─────────────────────┐
  │   on_success / on_failure) ─────▶ │ Events API                      │
  ├─ emit-metrics.py (custom         │ Metrics API v2                  │     ┌──────────────┐
  │   metrics: duration, failures, ─▶│ NOC pipeline board dashboard    │────▶│ NOC dashboard│
  │   rows_processed)                │ Alerting profiles (P1 / P2)     │     │  (running /  │
  └─ task logs ────────────────────▶ │ Problem notifications → webhook │────▶│  failed /    │
                                     └─────────────────────────────────┘     │  success)    │
                                     ┌─ Datadog ───────────────────────┐     └──────┬───────┘
                                     │ Metrics API v2                  │            │ P1–P5
                                     │ NOC pipeline board dashboard    │───────────▶│ routing
                                     │ Monitors (failure + duration    │            ▼
                                     │ SLO, priority 1–5)              │     Platform team /
                                     └─────────────────────────────────┘     Tier 2 support
```

Databricks-native monitoring (system tables, Lakehouse Monitoring) is covered in Chapter 10.
This repo is the *other* half: getting pipeline health into the enterprise platforms the NOC
already watches, with business criticality (P1–P5) driving who gets paged.

## Repository layout

| Path | Purpose |
|---|---|
| `terraform/envs/prod/` | Deployment root: `main.tf` instantiates the three modules with the prod pipeline list |
| `terraform/modules/dynatrace/` | NOC dashboard, P1/P2 alerting profiles, webhook problem notification |
| `terraform/modules/datadog/` | NOC dashboard, per-pipeline failure + duration-SLO monitors (priority 1–5) |
| `terraform/modules/databricks/` | Example `databricks_job` with `webhook_notifications` wired to destination IDs |
| `terraform/versions.tf`, `variables.tf`, `locals.tf` | Shared provider versions, variable shapes, P1–P5 mappings |
| `scripts/emit-metrics.py` | Databricks task that POSTs run metrics to Datadog + Dynatrace |
| `docs/p1-p5-severity-matrix.md` | The P1–P5 severity matrix: definitions, SLAs, escalation paths |

## Quickstart

1. **Export credentials** (never commit them — see `.gitignore`):
   ```bash
   export DATABRICKS_HOST="https://<workspace>.cloud.databricks.com"
   export DATABRICKS_TOKEN="<token>"
   export DYNATRACE_ENV_URL="https://<env>.live.dynatrace.com"
   export DYNATRACE_API_TOKEN="<token>"   # needs metrics.ingest, events.ingest, settings scopes
   export DD_API_KEY="<key>"
   export DD_APP_KEY="<key>"
   export DD_SITE="datadoghq.com"        # or datadoghq.eu
   ```

2. **Create webhook notification destinations in Databricks**: Admin Settings →
   Notification destinations → add three webhook destinations (on_start / on_success /
   on_failure) pointing at your ingest endpoint. Copy their IDs.

3. **Configure the env**:
   ```bash
   cd terraform/envs/prod
   cp terraform.tfvars.example terraform.tfvars   # fill in destination IDs + URLs
   ```

4. **Apply**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

5. **Emit metrics from jobs**: add `scripts/emit-metrics.py` as the final task of each
   pipeline (or call it from your existing final task). It reads the run context from
   environment variables and POSTs `databricks.pipeline.run.duration`,
   `databricks.pipeline.run.failed`, and `databricks.pipeline.rows_processed` to both
   platforms, tagged `pipeline`, `criticality`, `team`.

6. **Verify**: open the "NOC — Databricks Pipeline Status" board in Dynatrace and Datadog;
   trigger a test failure on a P4 pipeline and confirm the monitor fires without paging.

## Working on the dashboards

The checked-in dashboard JSON is a starting point. For complex boards, Dynatrace's own
docs recommend the export workflow: build the dashboard in the Dynatrace UI, then run
`terraform-provider-dynatrace -export` and commit the result back into
`terraform/modules/dynatrace/dashboards/`. The Datadog board can be edited in the UI and
re-exported via the Datadog API (`GET /api/v1/dashboard/<id>`).

## Provider docs

- Dynatrace: https://registry.terraform.io/providers/dynatrace-oss/dynatrace
- Datadog: https://registry.terraform.io/providers/DataDog/datadog
- Databricks: https://registry.terraform.io/providers/databricks/databricks

Where a provider schema detail is version-sensitive, the code carries a comment pointing
at the exact registry doc instead of guessing silently.
