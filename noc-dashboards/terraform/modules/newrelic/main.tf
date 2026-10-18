# NOC dashboard, NRQL alert policy/conditions, and notification routing.
#
# Dashboard workflow note: `newrelic_one_dashboard_json` takes the exact JSON
# export format of the New Relic UI (dashboard -> ... -> Copy JSON). Build
# complex boards in the UI and paste the export into
# dashboards/noc-pipeline-board.json. The __ACCOUNT_ID__ token below is
# replaced with var.account_id at plan time; every NRQL query in the export
# must reference it.
#
# Provider credentials come from NEW_RELIC_API_KEY / NEW_RELIC_ACCOUNT_ID env vars.

locals {
  pipeline_map = { for p in var.pipelines : p.name => p }

  # P1..P5 -> alert-condition tier. NRQL conditions only have critical/warning
  # blocks: P1/P2 get critical (pages), P3-P5 get warning (tickets) with a
  # longer evaluation window.
  nr_tier = {
    P1 = "critical"
    P2 = "critical"
    P3 = "warning"
    P4 = "warning"
    P5 = "warning"
  }

  crit_num = { for p in var.pipelines : p.name => substr(p.criticality, 1, 1) }

  dashboard_json = replace(
    file("${path.module}/dashboards/noc-pipeline-board.json"),
    "__ACCOUNT_ID__",
    tostring(var.account_id),
  )
}

resource "newrelic_one_dashboard_json" "noc_pipeline_board" {
  json = local.dashboard_json
}

resource "newrelic_alert_policy" "noc_databricks" {
  name                = "${var.environment}-databricks-pipelines"
  incident_preference = "PER_POLICY"
}

# Failure alert: any failed run in the last 15 minutes.
resource "newrelic_nrql_alert_condition" "pipeline_failure" {
  for_each = local.pipeline_map

  # Condition argument names (nrql.evaluation_offset, critical.threshold_*,
  # violation_time_limit_seconds) are version-sensitive — verify at
  # https://registry.terraform.io/providers/newrelic/newrelic
  # (resource newrelic_nrql_alert_condition).
  account_id                   = var.account_id
  policy_id                    = newrelic_alert_policy.noc_databricks.id
  type                         = "static"
  name                         = "[${each.value.criticality}] Databricks pipeline failed: ${each.key}"
  description                  = "Pager for P1/P2; ticket for P3-P5. NOC engages ${each.value.team} (Tier 2) per the P1-P5 matrix (docs/p1-p5-severity-matrix.md)."
  runbook_url                  = var.runbook_base_url == "" ? null : "${var.runbook_base_url}/pipelines/${each.key}"
  enabled                      = true
  violation_time_limit_seconds = 86400

  nrql {
    query             = "SELECT sum(databricks.pipeline.run.failed) FROM Metric WHERE pipeline = '${each.key}'"
    evaluation_offset = 3
  }

  dynamic "critical" {
    for_each = local.nr_tier[each.value.criticality] == "critical" ? [1] : []
    content {
      operator              = "above"
      threshold             = 0
      threshold_duration    = 300
      threshold_occurrences = "AT_LEAST_ONCE"
    }
  }

  dynamic "warning" {
    for_each = local.nr_tier[each.value.criticality] == "warning" ? [1] : []
    content {
      operator              = "above"
      threshold             = 0
      threshold_duration    = 900
      threshold_occurrences = "AT_LEAST_ONCE"
    }
  }
}

# Duration SLO: average run duration breaching the pipeline's SLA.
resource "newrelic_nrql_alert_condition" "pipeline_duration_slo" {
  for_each = local.pipeline_map

  account_id                   = var.account_id
  policy_id                    = newrelic_alert_policy.noc_databricks.id
  type                         = "static"
  name                         = "[${each.value.criticality}] Databricks pipeline breaching duration SLO: ${each.key}"
  description                  = "Average run duration over the last hour exceeded the ${each.value.sla_minutes}-minute SLO."
  runbook_url                  = var.runbook_base_url == "" ? null : "${var.runbook_base_url}/pipelines/${each.key}"
  enabled                      = true
  violation_time_limit_seconds = 86400

  nrql {
    query             = "SELECT average(databricks.pipeline.run.duration) FROM Metric WHERE pipeline = '${each.key}'"
    evaluation_offset = 3
  }

  dynamic "critical" {
    for_each = local.nr_tier[each.value.criticality] == "critical" ? [1] : []
    content {
      operator              = "above"
      threshold             = each.value.sla_minutes * 60
      threshold_duration    = 3600
      threshold_occurrences = "AT_LEAST_ONCE"
    }
  }

  dynamic "warning" {
    for_each = local.nr_tier[each.value.criticality] == "warning" ? [1] : []
    content {
      operator              = "above"
      threshold             = each.value.sla_minutes * 60
      threshold_duration    = 3600
      threshold_occurrences = "AT_LEAST_ONCE"
    }
  }
}

# P1/P2 -> PagerDuty. Destination/channel/workflow argument names
# (property.key/value, product="IINT", issues_filter.predicate) shifted across
# provider releases — verify against the newrelic registry docs for your pinned
# version before applying.
resource "newrelic_notification_destination" "pagerduty" {
  count      = var.pagerduty_integration_key == "" ? 0 : 1
  account_id = var.account_id
  name       = "${var.environment}-databricks-pagerduty"
  type       = "PAGERDUTY"

  property {
    key   = "integration_key"
    value = var.pagerduty_integration_key
  }
}

resource "newrelic_notification_channel" "pagerduty" {
  count          = var.pagerduty_integration_key == "" ? 0 : 1
  account_id     = var.account_id
  name           = "${var.environment}-databricks-pagerduty-channel"
  type           = "PAGERDUTY"
  destination_id = newrelic_notification_destination.pagerduty[0].id
  product        = "IINT"
}

resource "newrelic_workflow" "page_on_critical" {
  count                 = var.pagerduty_integration_key == "" ? 0 : 1
  account_id            = var.account_id
  name                  = "${var.environment}-databricks-page-critical"
  muting_rules_handling = "NOTIFY_ALL_ISSUES"

  issues_filter {
    name = "critical-databricks-pipelines"
    type = "FILTER"

    predicate {
      attribute = "priority"
      operator  = "EQUAL"
      values    = ["CRITICAL"]
    }
  }

  destination {
    channel_id = newrelic_notification_channel.pagerduty[0].id
  }
}

# P3-P5 -> NOC ticketing webhook.
resource "newrelic_notification_destination" "noc_webhook" {
  count      = var.noc_webhook_url == "" ? 0 : 1
  account_id = var.account_id
  name       = "${var.environment}-databricks-noc-webhook"
  type       = "WEBHOOK"

  property {
    key   = "url"
    value = var.noc_webhook_url
  }
}

resource "newrelic_notification_channel" "noc_webhook" {
  count          = var.noc_webhook_url == "" ? 0 : 1
  account_id     = var.account_id
  name           = "${var.environment}-databricks-noc-webhook-channel"
  type           = "WEBHOOK"
  destination_id = newrelic_notification_destination.noc_webhook[0].id
  product        = "IINT"
}

resource "newrelic_workflow" "ticket_on_warning" {
  count                 = var.noc_webhook_url == "" ? 0 : 1
  account_id            = var.account_id
  name                  = "${var.environment}-databricks-ticket-warning"
  muting_rules_handling = "NOTIFY_ALL_ISSUES"

  issues_filter {
    name = "warning-databricks-pipelines"
    type = "FILTER"

    predicate {
      attribute = "priority"
      operator  = "EQUAL"
      values    = ["HIGH"]
    }
  }

  destination {
    channel_id = newrelic_notification_channel.noc_webhook[0].id
  }
}

output "dashboard_guid" {
  value       = newrelic_one_dashboard_json.noc_pipeline_board.guid
  description = "GUID of the NOC pipeline status dashboard."
}

output "alert_policy_id" {
  value       = newrelic_alert_policy.noc_databricks.id
  description = "ID of the Databricks pipelines alert policy."
}
