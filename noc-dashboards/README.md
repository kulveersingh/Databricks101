# Databricks NOC Dashboards — Terraform Automation

Companion infrastructure for **Chapter 19 ("The NOC Dashboard")** of *Databricks Internals*.
This package creates, via
Terraform, the Dynatrace, Datadog, New Relic, and Splunk dashboards, P1–P5 alerting, and Databricks webhook wiring
that put Databricks pipeline run status (running / failed / success) on the NOC's screens.

## Why four platforms

Enterprises standardize on one observability platform; the four modules are
**drop-in alternatives, not a bundle you run all four of.** Pick the module that
matches the platform your NOC already watches and leave the rest disabled
(`enable_<platform> = false`). Every module consumes the same `pipelines` list
and the same P1–P5 semantics, so switching platforms later is a module swap, not
a redesign.

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
| `terraform/envs/prod/` | Deployment root: `main.tf` instantiates the five modules with the prod pipeline list |
| `terraform/modules/dynatrace/` | NOC dashboard, P1/P2 alerting profiles, webhook problem notification |
| `terraform/modules/datadog/` | NOC dashboard, per-pipeline failure + duration-SLO monitors (priority 1–5) |
| `terraform/modules/newrelic/` | NOC dashboard, NRQL alert policy/conditions (critical for P1/P2, warning for P3–P5), PagerDuty + webhook routing |
| `terraform/modules/splunk/` | Simple XML NOC dashboard, per-pipeline saved-search alerts (severity 1–5 from P1–P5), webhook actions |
| `terraform/modules/databricks/` | Example `databricks_job` with `webhook_notifications` wired to destination IDs |
| `terraform/versions.tf`, `variables.tf`, `locals.tf` | Shared provider versions, variable shapes, P1–P5 mappings |
| `scripts/emit-metrics.py` | Databricks task that POSTs run metrics to Datadog, Dynatrace, New Relic, and Splunk HEC |
| `scripts/deploy-splunk-dashboard.sh` | Fallback: deploy the Splunk Simple XML dashboard via REST when the provider can't |
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
   export NEW_RELIC_API_KEY="<key>"
   export NEW_RELIC_ACCOUNT_ID="<account-id>"   # NEW_RELIC_API_REGION=eu for the EU data center
   export SPLUNK_HOST="splunk.example.com:8089"
   export SPLUNK_TOKEN="<token>"                # or SPLUNK_USERNAME / SPLUNK_PASSWORD
   export SPLUNK_HEC_HOST="splunk.example.com:8088"
   export SPLUNK_HEC_TOKEN="<hec-token>"
   export SPLUNK_HEC_INDEX="databricks"         # SPLUNK_HEC_SOURCETYPE defaults to databricks:pipeline
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
   `databricks.pipeline.run.failed`, and `databricks.pipeline.rows_processed` to all
   four platforms (Splunk gets one HEC event per run), tagged `pipeline`,
   `criticality`, `team`.

6. **Verify**: open the "NOC — Databricks Pipeline Status" board in each enabled
   platform; trigger a test failure on a P4 pipeline and confirm the monitor fires
   without paging. If the `splunk/splunk` provider cannot deploy the dashboard on
   your tenant, use `scripts/deploy-splunk-dashboard.sh` instead.

## Working on the dashboards

The checked-in dashboard definitions are starting points. For complex boards, build in
the UI and export back:
- Dynatrace: `terraform-provider-dynatrace -export` into `terraform/modules/dynatrace/dashboards/`.
- Datadog: `GET /api/v1/dashboard/<id>` into `terraform/modules/datadog/dashboards/`.
- New Relic: dashboard -> ... -> Copy JSON into
  `terraform/modules/newrelic/dashboards/noc-pipeline-board.json` (keep the
  `__ACCOUNT_ID__` token in every NRQL query).
- Splunk: edit the Simple XML in the UI's source editor, then commit back into
  `terraform/modules/splunk/dashboards/noc-pipeline-board.xml`.

## Provider docs

- Dynatrace: https://registry.terraform.io/providers/dynatrace-oss/dynatrace
- Datadog: https://registry.terraform.io/providers/DataDog/datadog
- Databricks: https://registry.terraform.io/providers/databricks/databricks
- New Relic: https://registry.terraform.io/providers/newrelic/newrelic
- Splunk (community): https://registry.terraform.io/providers/splunk/splunk

Where a provider schema detail is version-sensitive, the code carries a comment pointing
at the exact registry doc instead of guessing silently.
