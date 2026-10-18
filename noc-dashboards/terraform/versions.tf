# Shared provider requirements. Each env root (terraform/envs/*) repeats this block;
# keep the three in sync. Pin versions in production.
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
  }
}
