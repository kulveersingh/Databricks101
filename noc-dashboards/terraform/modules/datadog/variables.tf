variable "environment" {
  type        = string
  description = "Environment name, used as a prefix for all created resources."
}

variable "pipelines" {
  type = list(object({
    name        = string
    criticality = string
    team        = string
    sla_minutes = number
  }))
  description = "Databricks pipelines surfaced on the NOC dashboard and monitors."
}

variable "runbook_base_url" {
  type        = string
  default     = ""
  description = "Base URL for per-pipeline runbooks, linked from monitor messages."
}
