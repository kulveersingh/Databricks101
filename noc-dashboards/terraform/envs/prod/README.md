# prod environment

## Deploy

```bash
# 1. Credentials (env vars only — never in tfvars)
export DATABRICKS_HOST="https://<workspace>.cloud.databricks.com"
export DATABRICKS_TOKEN="<token>"
export DYNATRACE_ENV_URL="https://<env>.live.dynatrace.com"
export DYNATRACE_API_TOKEN="<token>"
export DD_API_KEY="<key>"
export DD_APP_KEY="<key>"
export DD_SITE="datadoghq.com"
export NEW_RELIC_API_KEY="<key>"
export NEW_RELIC_ACCOUNT_ID="<account-id>"
export SPLUNK_HOST="splunk.example.com:8089"
export SPLUNK_TOKEN="<token>"          # or SPLUNK_USERNAME / SPLUNK_PASSWORD
export SPLUNK_HEC_HOST="splunk.example.com:8088"
export SPLUNK_HEC_TOKEN="<hec-token>"
export SPLUNK_HEC_INDEX="databricks"   # SPLUNK_HEC_SOURCETYPE defaults to databricks:pipeline

# 2. Notification destinations in Databricks (Admin Settings ->
#    Notification destinations): create webhook destinations for
#    on_start / on_success / on_failure and copy their IDs.

# 3. Configure
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars with real IDs/URLs

# 4. Apply
terraform init
terraform plan
terraform apply
```

## Verify

1. Open "NOC - Databricks Pipeline Status" in Dynatrace, Datadog, New Relic, and
   Splunk (dashboard name `noc_databricks_pipeline_status`).
2. Run `scripts/emit-metrics.py` once manually with test env vars and confirm the
   `databricks.pipeline.*` metrics appear in all four platforms (Splunk events
   land in the HEC index).
3. Force a test failure on `marketing-aggregates` (P4): the Datadog monitor and
   New Relic warning condition should fire ticket-class alerts without paging.
4. If the `splunk/splunk` provider cannot manage dashboards on your tenant, deploy
   the dashboard with `scripts/deploy-splunk-dashboard.sh` instead.

## Disable one platform

Set `enable_dynatrace = false` (or `enable_datadog`, `enable_newrelic`,
`enable_splunk`) in `terraform.tfvars` to skip that platform's resources.
