# Prod deployment root for the Databricks NOC dashboards.
#
# Mirrors terraform/versions.tf, terraform/variables.tf and terraform/locals.tf
# (the shared contract); keep shapes in sync when either changes.
#
# Credentials are env-var only:
#   DATABRICKS_HOST / DATABRICKS_TOKEN
#   DYNATRACE_ENV_URL / DYNATRACE_API_TOKEN
#   DD_API_KEY / DD_APP_KEY (+ DD_SITE)

terraform {
  required_version = ">= 1.5"

  required_providers {
    dynatrace = {
      source = "dynatrace-oss/dynatrace"
    }
    datadog = {
      source = "DataDog/datadog"
    }
    databricks = {
      source = "databricks/databricks"
    }
  }
}

provider "databricks" {}
provider "dynatrace" {}
provider "datadog" {}

variable "databricks_webhook_ids" {
  type = object({
    on_start   = string
    on_success = string
    on_failure = string
  })
  description = "Notification-destination IDs from Databricks Admin Settings."
}

variable "noc_webhook_url" {
  type        = string
  sensitive   = true
  default     = ""
  description = "NOC endpoint for Dynatrace problem notifications. Empty disables the notification."
}

variable "runbook_base_url" {
  type        = string
  default     = ""
  description = "Base URL for per-pipeline runbooks linked from alerts."
}

variable "fraud_notebook_path" {
  type        = string
  description = "Workspace path of the fraud-detection notebook."
}

variable "enable_dynatrace" {
  type    = bool
  default = true
}

variable "enable_datadog" {
  type    = bool
  default = true
}

locals {
  environment = "prod"

  pipelines = [
    { name = "fraud-detection",           criticality = "P1", team = "platform", sla_minutes = 15 },
    { name = "ledger-bronze-silver-gold", criticality = "P1", team = "platform", sla_minutes = 60 },
    { name = "aml-nightly-scoring",       criticality = "P2", team = "risk",     sla_minutes = 120 },
    { name = "risk-month-end-report",     criticality = "P3", team = "risk",     sla_minutes = 480 },
    { name = "marketing-aggregates",      criticality = "P4", team = "cx",       sla_minutes = 1440 },
  ]
}

module "dynatrace" {
  source          = "../../modules/dynatrace"
  count           = var.enable_dynatrace ? 1 : 0
  environment     = local.environment
  pipelines       = local.pipelines
  noc_webhook_url = var.noc_webhook_url
}

module "datadog" {
  source           = "../../modules/datadog"
  count            = var.enable_datadog ? 1 : 0
  environment      = local.environment
  pipelines        = local.pipelines
  runbook_base_url = var.runbook_base_url
}

module "databricks_jobs" {
  source                 = "../../modules/databricks"
  environment            = local.environment
  job_name               = "fraud-detection"
  notebook_path          = var.fraud_notebook_path
  webhook_ids            = var.databricks_webhook_ids
  quartz_cron_expression = "0 */15 * * * ?"
  criticality            = "P1"
  team                   = "platform"
}

output "dynatrace_dashboard_id" {
  value       = var.enable_dynatrace ? module.dynatrace[0].dashboard_id : null
  description = "NOC dashboard ID in Dynatrace."
}

output "datadog_monitor_ids" {
  value       = var.enable_datadog ? module.datadog[0].monitor_ids : null
  description = "Datadog monitor IDs keyed by pipeline name."
}

output "fraud_job_id" {
  value       = module.databricks_jobs.job_id
  description = "Databricks job ID for fraud-detection."
}
