# NOC dashboard plus per-pipeline failure and duration-SLO monitors.
# Provider credentials come from DD_API_KEY / DD_APP_KEY (and DD_SITE) env vars.

locals {
  dd_priority = {
    P1 = 1
    P2 = 2
    P3 = 3
    P4 = 4
    P5 = 5
  }

  pipeline_map = { for p in var.pipelines : p.name => p }

  # P1 -> "1", P2 -> "2", ... for the message text.
  crit_num = { for p in var.pipelines : p.name => substr(p.criticality, 1, 1) }
}

resource "datadog_dashboard_json" "noc_pipeline_board" {
  dashboard = file("${path.module}/dashboards/noc-pipeline-board.json")
}

# Failure alert: any failed run in the last 15 minutes.
resource "datadog_monitor" "pipeline_failure" {
  for_each = local.pipeline_map

  name = "[${each.value.criticality}] Databricks pipeline failed: ${each.key}"
  type = "metric alert"
  query = "sum(last_15m):sum:databricks.pipeline.run.failed{pipeline:${each.key}} > 0"

  message = <<-EOT
    @pagerduty-${each.value.team} [P${local.crit_num[each.key]}] Databricks pipeline **${each.key}** reported failures in the last 15m.
    Runbook: ${var.runbook_base_url}/pipelines/${each.key}
    NOC: acknowledge within SLA, then engage ${each.value.team} (Tier 2) per the P1-P5 matrix (docs/p1-p5-severity-matrix.md).
  EOT

  monitor_thresholds {
    critical = 1
  }

  priority         = local.dd_priority[each.value.criticality]
  include_tags     = true
  notify_no_data   = true # a scheduled run that never starts is as bad as a failed one
  no_data_timeframe = 30

  tags = [
    "team:${each.value.team}",
    "criticality:${each.value.criticality}",
    "service:databricks",
    "source:terraform",
    "env:${var.environment}",
  ]
}

# Duration SLO: average run duration breaching the pipeline's SLA.
resource "datadog_monitor" "pipeline_duration_slo" {
  for_each = local.pipeline_map

  name  = "[${each.value.criticality}] Databricks pipeline breaching duration SLO: ${each.key}"
  type  = "metric alert"
  query = "avg(last_1h):avg:databricks.pipeline.run.duration{pipeline:${each.key}} > ${each.value.sla_minutes * 60}"

  message = <<-EOT
    @pagerduty-${each.value.team} [P${local.crit_num[each.key]}] Pipeline **${each.key}** avg run duration breached its ${each.value.sla_minutes}-minute SLO.
    Runbook: ${var.runbook_base_url}/pipelines/${each.key}
  EOT

  monitor_thresholds {
    warning  = each.value.sla_minutes * 60 * 0.8
    critical = each.value.sla_minutes * 60
  }

  priority     = local.dd_priority[each.value.criticality]
  include_tags = true

  tags = [
    "team:${each.value.team}",
    "criticality:${each.value.criticality}",
    "service:databricks",
    "source:terraform",
    "env:${var.environment}",
  ]
}

output "monitor_ids" {
  value = {
    failure       = { for k, m in datadog_monitor.pipeline_failure : k => m.id }
    duration_slo  = { for k, m in datadog_monitor.pipeline_duration_slo : k => m.id }
  }
  description = "Datadog monitor IDs keyed by pipeline name."
}
