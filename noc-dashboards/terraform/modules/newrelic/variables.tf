variable "environment" {
  type        = string
  description = "Environment name, used as a prefix for all created resources."
}

variable "account_id" {
  type        = number
  description = "New Relic account ID. Also set NEW_RELIC_ACCOUNT_ID for the provider."
}

variable "pipelines" {
  type = list(object({
    name        = string
    criticality = string
    team        = string
    sla_minutes = number
  }))
  description = "Databricks pipelines surfaced on the NOC dashboard and alerts."
}

variable "runbook_base_url" {
  type        = string
  default     = ""
  description = "Base URL for per-pipeline runbooks, linked from alert conditions."
}

variable "pagerduty_integration_key" {
  type        = string
  sensitive   = true
  default     = ""
  description = "PagerDuty Events API v2 integration key for P1/P2 pages. Empty disables PagerDuty routing."
}

variable "noc_webhook_url" {
  type        = string
  sensitive   = true
  default     = ""
  description = "NOC ticketing endpoint receiving P3-P5 webhook notifications. Empty disables the webhook."
}
