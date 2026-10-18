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

  # Business criticality -> New Relic condition tier. NRQL conditions only
  # have critical/warning blocks; P3-P5 use warning with longer evaluation
  # windows so they ticket instead of page.
  nr_tier = {
    P1 = "critical"
    P2 = "critical"
    P3 = "warning"
    P4 = "warning"
    P5 = "warning"
  }

  # Business criticality -> Splunk alert severity
  # (1=DEBUG, 2=INFO, 3=WARN, 4=ERROR, 5=SEVERE, 6=FATAL).
  splunk_severity = {
    P1 = 5
    P2 = 4
    P3 = 3
    P4 = 2
    P5 = 1
  }
}
