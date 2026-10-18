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
  description = "Databricks pipelines surfaced on the NOC dashboard."
}

variable "noc_webhook_url" {
  type        = string
  sensitive   = true
  description = "NOC endpoint receiving Dynatrace problem notifications (webhook)."
}
