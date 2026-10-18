#!/usr/bin/env bash
# Fallback deploy of the NOC Simple XML dashboard via the Splunk REST API.
#
# Use this INSTEAD OF terraform/modules/splunk's splunk_dashboards resource when
# the splunk/splunk community provider is unavailable for your platform, its
# dashboard resource schema has drifted, or your Splunk Cloud tenant does not
# allow the provider's management port. It POSTs the same Simple XML
# (terraform/modules/splunk/dashboards/noc-pipeline-board.xml) to:
#
#   POST https://<SPLUNK_HOST>/servicesNS/nobody/<APP>/data/ui/views
#
# Required env:
#   SPLUNK_HOST   host:port of the Splunk management endpoint (e.g. splunk.example.com:8089)
#   SPLUNK_APP    app namespace for the dashboard (default: databricks_noc)
# Auth (one of):
#   SPLUNK_TOKEN                    bearer token (preferred)
#   SPLUNK_USERNAME / SPLUNK_PASSWORD
#
# Example:
#   SPLUNK_HOST=splunk.example.com:8089 SPLUNK_TOKEN=<token> \
#     ./scripts/deploy-splunk-dashboard.sh

set -euo pipefail

HOST="${SPLUNK_HOST:?SPLUNK_HOST is required (host:port)}"
APP="${SPLUNK_APP:-databricks_noc}"
XML="$(dirname "$0")/../terraform/modules/splunk/dashboards/noc-pipeline-board.xml"

if [[ ! -f "$XML" ]]; then
  echo "deploy-splunk-dashboard: dashboard XML not found at $XML" >&2
  exit 2
fi

AUTH=()
if [[ -n "${SPLUNK_TOKEN:-}" ]]; then
  AUTH=(-H "Authorization: Bearer $SPLUNK_TOKEN")
elif [[ -n "${SPLUNK_USERNAME:-}" && -n "${SPLUNK_PASSWORD:-}" ]]; then
  AUTH=(-u "$SPLUNK_USERNAME:$SPLUNK_PASSWORD")
else
  echo "deploy-splunk-dashboard: set SPLUNK_TOKEN or SPLUNK_USERNAME/SPLUNK_PASSWORD" >&2
  exit 2
fi

URL="https://${HOST}/servicesNS/nobody/${APP}/data/ui/views"

echo "deploy-splunk-dashboard: POST ${URL} (app=${APP})"
HTTP_CODE="$(curl -sk -o /tmp/splunk-deploy-resp.txt -w '%{http_code}' "${AUTH[@]}" \
  --data-urlencode "name=noc_databricks_pipeline_status" \
  --data-urlencode "eai:data@$XML" \
  "$URL")"

if [[ "$HTTP_CODE" == "201" ]]; then
  echo "deploy-splunk-dashboard: dashboard created (201)"
elif [[ "$HTTP_CODE" == "409" ]]; then
  echo "deploy-splunk-dashboard: dashboard exists (409) — updating in place"
  HTTP_CODE="$(curl -sk -o /tmp/splunk-deploy-resp.txt -w '%{http_code}' -X POST "${AUTH[@]}" \
    --data-urlencode "eai:data@$XML" \
    "${URL}/noc_databricks_pipeline_status")"
  echo "deploy-splunk-dashboard: update -> $HTTP_CODE"
  cat /tmp/splunk-deploy-resp.txt
else
  echo "deploy-splunk-dashboard: failed -> $HTTP_CODE"
  cat /tmp/splunk-deploy-resp.txt
  exit 1
fi
