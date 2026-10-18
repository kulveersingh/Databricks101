# NOC dashboard (Simple XML) and per-pipeline saved-search alerts.
#
# Provider note: splunk/splunk is a community provider and its resource
# schemas have moved between releases. Argument names below (eai_data,
# alert_severity, action_* ) MUST be verified against the pinned provider
# version at https://registry.terraform.io/providers/splunk/splunk before
# applying. If the provider cannot manage dashboards on your Splunk Cloud
# tenant, use scripts/deploy-splunk-dashboard.sh (direct REST) instead of
# splunk_dashboards.
#
# Provider credentials come from SPLUNK_HOST (+ SPLUNK_TOKEN or
# SPLUNK_USERNAME/SPLUNK_PASSWORD) env vars.

locals {
  pipeline_map = { for p in var.pipelines : p.name => p }

  # P1..P5 -> Splunk alert severity (1=DEBUG, 2=INFO, 3=WARN, 4=ERROR,
  # 5=SEVERE, 6=FATAL). P1 pages, P2 alerts loudly, P3-P5 file tickets.
  splunk_severity = {
    P1 = 5
    P2 = 4
    P3 = 3
    P4 = 2
    P5 = 1
  }

  crit_num = { for p in var.pipelines : p.name => substr(p.criticality, 1, 1) }
}

# NOC status board. The resource takes the raw Simple XML via file();
# keep dashboards/noc-pipeline-board.xml valid XML (validated in CI).
resource "splunk_dashboards" "noc_pipeline_board" {
  name     = "noc_databricks_pipeline_status"
  eai_data = file("${path.module}/dashboards/noc-pipeline-board.xml")
}

# Failure alert: any failed run in the last 15 minutes, evaluated every 5.
resource "splunk_saved_searches" "pipeline_failure" {
  for_each = local.pipeline_map

  # Saved-search argument names (cron_schedule, alert_severity, actions,
  # action_webhook_param_url) vary by provider release — verify against the
  # pinned splunk/splunk docs before applying.
  name          = "${var.environment}-databricks-${each.key}-failure"
  search        = "index=${var.splunk_index} sourcetype=${var.splunk_sourcetype} pipeline=${each.key} earliest=-15m | stats sum(failed) as failures | where failures > 0"
  cron_schedule = "*/5 * * * *"

  alert_severity = local.splunk_severity[each.value.criticality]
  description    = "[P${local.crit_num[each.key]}] ${each.key}: failures in last 15m. NOC engages ${each.value.team} (Tier 2) per docs/p1-p5-severity-matrix.md. Runbook: ${var.runbook_base_url}/pipelines/${each.key}"

  actions                    = "webhook"
  action_webhook_param_url   = var.noc_webhook_url
  alert_suppress             = true
  alert_suppress_fields      = "pipeline"
  alert_suppress_period      = "30m"
}

# Duration SLO: average run duration breaching the pipeline's SLA.
resource "splunk_saved_searches" "pipeline_duration_slo" {
  for_each = local.pipeline_map

  name          = "${var.environment}-databricks-${each.key}-duration-slo"
  search        = "index=${var.splunk_index} sourcetype=${var.splunk_sourcetype} pipeline=${each.key} earliest=-1h | stats avg(duration_sec) as avg_dur | where avg_dur > ${each.value.sla_minutes * 60}"
  cron_schedule = "0 * * * *"

  alert_severity = local.splunk_severity[each.value.criticality]
  description    = "[P${local.crit_num[each.key]}] ${each.key}: avg run duration breached the ${each.value.sla_minutes}-minute SLO. Runbook: ${var.runbook_base_url}/pipelines/${each.key}"

  actions                    = "webhook"
  action_webhook_param_url   = var.noc_webhook_url
  alert_suppress             = true
  alert_suppress_fields      = "pipeline"
  alert_suppress_period      = "1h"
}

output "dashboard_name" {
  value       = splunk_dashboards.noc_pipeline_board.name
  description = "Name of the NOC pipeline status dashboard in Splunk."
}

output "saved_search_names" {
  value = {
    failure      = { for k, s in splunk_saved_searches.pipeline_failure : k => s.name }
    duration_slo = { for k, s in splunk_saved_searches.pipeline_duration_slo : k => s.name }
  }
  description = "Splunk saved-search alert names keyed by pipeline name."
}
