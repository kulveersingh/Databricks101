variable "environment" {
  type        = string
  description = "Environment name, used as a prefix for all created resources."
}

variable "pipelines" {
  type = list(object({
    name        = string # databricks job name; also the metric tag value
    criticality = string # P1..P5 — see docs/p1-p5-severity-matrix.md
    team        = string # owning team; used for paging handles and tags
    sla_minutes = number # duration SLO for the pipeline's main run
  }))
  description = "Databricks pipelines surfaced on the NOC dashboards."

  validation {
    condition     = alltrue([for p in var.pipelines : contains(["P1", "P2", "P3", "P4", "P5"], p.criticality)])
    error_message = "Each pipeline criticality must be one of P1..P5."
  }
}

variable "databricks_webhook_ids" {
  type = object({
    on_start   = string
    on_success = string
    on_failure = string
  })
  description = <<-EOT
    Notification-destination IDs for Databricks job webhooks. The destinations
    themselves are created in Databricks Admin Settings -> Notification
    destinations; this variable only carries their IDs.
  EOT
}

variable "noc_webhook_url" {
  type        = string
  sensitive   = true
  default     = ""
  description = "NOC endpoint receiving Dynatrace problem notifications (webhook)."
}

variable "runbook_base_url" {
  type        = string
  default     = ""
  description = "Base URL for per-pipeline runbooks, linked from alerts."
}

variable "enable_dynatrace" {
  type        = bool
  default     = true
  description = "Create Dynatrace dashboards, alerting profiles and notifications."
}

variable "enable_datadog" {
  type        = bool
  default     = true
  description = "Create Datadog dashboards and monitors."
}

variable "enable_newrelic" {
  type        = bool
  default     = true
  description = "Create New Relic dashboards, alert policies/conditions and notification routing."
}

variable "enable_splunk" {
  type        = bool
  default     = true
  description = "Create Splunk dashboards and saved-search alerts."
}
