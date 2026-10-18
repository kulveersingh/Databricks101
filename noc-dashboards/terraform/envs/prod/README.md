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

1. Open "NOC - Databricks Pipeline Status" in Dynatrace and Datadog.
2. Run `scripts/emit-metrics.py` once manually with test env vars and confirm the
   `databricks.pipeline.*` metrics appear in both platforms.
3. Force a test failure on `marketing-aggregates` (P4): the Datadog monitor should
   fire a ticket-class alert without paging anyone.

## Disable one platform

Set `enable_dynatrace = false` (or `enable_datadog = false`) in `terraform.tfvars`
to skip that platform's resources.
