variable "environment" {
  type        = string
  description = "Environment name, used as a prefix for the job name."
}

variable "job_name" {
  type        = string
  description = "Pipeline/job name (e.g. fraud-detection)."
}

variable "notebook_path" {
  type        = string
  description = "Workspace path of the notebook implementing the pipeline task."
}

variable "webhook_ids" {
  type = object({
    on_start   = string
    on_success = string
    on_failure = string
  })
  description = <<-EOT
    Notification-destination IDs for job webhooks. Destinations are created in
    Databricks Admin Settings -> Notification destinations; only their IDs
    are passed here.
  EOT
}

variable "quartz_cron_expression" {
  type        = string
  default     = "0 */15 * * * ?"
  description = "Quartz cron schedule for the job."
}

variable "criticality" {
  type        = string
  default     = "P1"
  description = "P1..P5 business criticality, applied as a job tag."
}

variable "team" {
  type        = string
  default     = "platform"
  description = "Owning team, applied as a job tag."
}
