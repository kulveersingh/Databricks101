locals {
  # P1..P5 -> Datadog monitor priority (1 = highest).
  dd_priority = {
    P1 = 1
    P2 = 2
    P3 = 3
    P4 = 4
    P5 = 5
  }

  # Business criticality -> Dynatrace alerting-profile event severity.
  # Dynatrace severity levels describe the event kind, not business impact;
  # P1/P2 get dedicated alerting profiles, P3-P5 share the catch-all.
  dt_severity = {
    P1 = "AVAILABILITY"
    P2 = "ERROR"
    P3 = "PERFORMANCE"
    P4 = "CUSTOM_ALERT"
    P5 = "CUSTOM_ALERT"
  }

  monitor_name_prefix = "${var.environment}-databricks"
}
