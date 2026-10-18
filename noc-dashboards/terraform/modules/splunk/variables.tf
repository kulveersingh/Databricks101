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
  description = "Databricks pipelines surfaced on the NOC dashboard and alerts."
}

variable "runbook_base_url" {
  type        = string
  default     = ""
  description = "Base URL for per-pipeline runbooks, linked from alert descriptions."
}

variable "splunk_app" {
  type        = string
  default     = "databricks_noc"
  description = "Splunk app namespace the dashboard is deployed into."
}

variable "splunk_index" {
  type        = string
  default     = "databricks"
  description = "Splunk index holding databricks pipeline events (written by emit-metrics.py HEC path)."
}

variable "splunk_sourcetype" {
  type        = string
  default     = "databricks:pipeline"
  description = "Sourcetype of the pipeline events in Splunk."
}

variable "noc_webhook_url" {
  type        = string
  sensitive   = true
  default     = ""
  description = "NOC endpoint receiving Splunk webhook alerts. Empty disables alert actions."
}
