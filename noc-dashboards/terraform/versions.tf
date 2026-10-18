# Shared provider requirements. Each env root (terraform/envs/*) repeats this block;
# keep the five in sync. Pin versions in production.
terraform {
  required_version = ">= 1.5"

  required_providers {
    # https://registry.terraform.io/providers/dynatrace-oss/dynatrace
    dynatrace = {
      source = "dynatrace-oss/dynatrace"
    }
    # https://registry.terraform.io/providers/DataDog/datadog
    datadog = {
      source = "DataDog/datadog"
    }
    # https://registry.terraform.io/providers/databricks/databricks
    databricks = {
      source = "databricks/databricks"
    }
    # https://registry.terraform.io/providers/newrelic/newrelic
    newrelic = {
      source = "newrelic/newrelic"
    }
    # https://registry.terraform.io/providers/splunk/splunk
    # Community provider — pin a release and verify resource schemas.
    splunk = {
      source = "splunk/splunk"
    }
  }
}
