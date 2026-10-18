# Example Databricks job with webhook notifications wired to the notification
# destinations created in Admin Settings -> Notification destinations.
#
# Webhook event types emitted by Databricks jobs: jobs.on_start,
# jobs.on_success, jobs.on_failure, jobs.on_duration_warning_threshold_exceeded.
# Map these to Dynatrace (Events API) / Datadog (events) in your ingest
# endpoint, or consume them directly as problem/metric triggers.

resource "databricks_job" "pipeline" {
  name = "${var.environment}-${var.job_name}"

  webhook_notifications {
    on_start {
      id = var.webhook_ids.on_start
    }
    on_success {
      id = var.webhook_ids.on_success
    }
    on_failure {
      id = var.webhook_ids.on_failure
    }
  }

  task {
    task_key = "main"
    notebook_task {
      notebook_path = var.notebook_path
    }
  }

  schedule {
    quartz_cron_expression = var.quartz_cron_expression
    pause_status           = "UNPAUSED"
  }

  tags = {
    criticality = var.criticality
    team        = var.team
  }
}

output "job_id" {
  value       = databricks_job.pipeline.job_id
  description = "Databricks job ID."
}
