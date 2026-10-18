# NOC dashboard, P1/P2 alerting profiles, and webhook problem notification.
#
# Dashboard workflow note (per Dynatrace docs): complex boards are easiest to
# build in the Dynatrace UI and then export with `terraform-provider-dynatrace
# -export`; commit the result back into dashboards/ and split metadata/tiles
# as done below.

locals {
  board = jsondecode(file("${path.module}/dashboards/noc-pipeline-board.json"))
}

resource "dynatrace_dashboard" "noc_pipeline_board" {
  # The provider takes dashboard_metadata and tiles as separate JSON strings.
  dashboard_metadata = jsonencode(local.board.metadata)
  tiles              = jsonencode(local.board.tiles)
}

# P1: page immediately. Tag filter scopes the profile to P1 pipeline entities
# (tagged criticality:P1 via metric dimensions / entity tags).
resource "dynatrace_alerting_profile" "p1" {
  display_name = "${var.environment}-databricks-pipelines-P1"

  rules {
    severity_level   = "AVAILABILITY"
    delay_in_minutes = 0
    tag_filter {
      include_mode = "INCLUDE"
      # Tag selection syntax for the installed provider version — verify at
      # https://registry.terraform.io/providers/dynatrace-oss/dynatrace
      # (resource dynatrace_alerting_profile, rules.tag_filter).
      tags {
        context = "CONTEXTLESS"
        key     = "criticality"
        value   = "P1"
      }
    }
  }
}

# P2: page, with a short delay to absorb flapping.
resource "dynatrace_alerting_profile" "p2" {
  display_name = "${var.environment}-databricks-pipelines-P2"

  rules {
    severity_level   = "ERROR"
    delay_in_minutes = 5
    tag_filter {
      include_mode = "INCLUDE"
      tags {
        context = "CONTEXTLESS"
        key     = "criticality"
        value   = "P2"
      }
    }
  }
}

# Route P1 problems to the NOC webhook. Webhook payload fields have shifted
# between provider releases — verify against the registry docs for
# dynatrace_notification in your pinned provider version before applying.
resource "dynatrace_notification" "noc_webhook" {
  count            = var.noc_webhook_url == "" ? 0 : 1
  name             = "${var.environment}-databricks-noc-webhook"
  active           = true
  alerting_profile = dynatrace_alerting_profile.p1.id

  webhook {
    url                    = var.noc_webhook_url
    accept_any_certificate = false
    payload                = "{\"problem_id\":\"{ProblemID}\",\"title\":\"{ProblemTitle}\",\"severity\":\"{SeverityLevel}\",\"impacted_entity\":\"{ImpactedEntity}\"}"
  }
}

output "dashboard_id" {
  value       = dynatrace_dashboard.noc_pipeline_board.id
  description = "ID of the NOC pipeline status dashboard."
}

output "alerting_profile_ids" {
  value = {
    p1 = dynatrace_alerting_profile.p1.id
    p2 = dynatrace_alerting_profile.p2.id
  }
  description = "Alerting profile IDs for P1 and P2 pipelines."
}
