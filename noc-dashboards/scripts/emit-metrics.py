#!/usr/bin/env python3
"""Emit Databricks pipeline run metrics to Datadog and Dynatrace.

Intended as the final task of a Lakeflow job (or called from it). Reads the run
context from environment variables, then POSTs custom metrics to both platforms:

  databricks.pipeline.run.duration        (gauge, seconds)
  databricks.pipeline.run.failed          (count, 1 on failure else 0)
  databricks.pipeline.rows_processed      (count)

All metrics carry tags/dimensions: pipeline, criticality, team, run_id.

Configuration is env-var only; no secrets are hardcoded.

Required env:
  DD_API_KEY, DD_SITE            (Datadog; DD_APP_KEY not needed for metrics ingest)
  DYNATRACE_ENV_URL, DYNATRACE_API_TOKEN
Run context env:
  PIPELINE_NAME, RUN_ID, RUN_STATUS (SUCCESS|FAILED|...), RUN_DURATION_SEC,
  ROWS_PROCESSED, PIPELINE_CRITICALITY (P1..P5), PIPELINE_TEAM
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error


def env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        print(f"emit-metrics: missing required env var {name}", file=sys.stderr)
        sys.exit(2)
    return value


def post_json(url, payload, headers):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        print(f"emit-metrics: POST {url} -> HTTP {e.code}: {e.read().decode()[:500]}",
              file=sys.stderr)
        return e.code


def post_text(url, body, headers):
    req = urllib.request.Request(url, data=body.encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        print(f"emit-metrics: POST {url} -> HTTP {e.code}: {e.read().decode()[:500]}",
              file=sys.stderr)
        return e.code


def send_datadog(api_key, site, series):
    # Datadog Metrics API v2: https://docs.datadoghq.com/api/latest/metrics/#submit-metrics
    url = f"https://api.{site}/api/v2/series"
    return post_json(url, {"series": series}, {
        "Content-Type": "application/json",
        "DD-API-KEY": api_key,
    })


def send_dynatrace(env_url, api_token, lines):
    # Dynatrace Metrics API v2 ingest (line protocol):
    # https://www.dynatrace.com/support/help/dynatrace-api/environment-api/metric-v2/post-ingest-metrics
    url = f"{env_url.rstrip('/')}/api/v2/metrics/ingest"
    return post_text(url, "\n".join(lines), {
        "Content-Type": "text/plain; charset=utf-8",
        "Authorization": f"Api-Token {api_token}",
    })


def main():
    pipeline = env("PIPELINE_NAME", required=True)
    run_id = env("RUN_ID", default="unknown")
    status = env("RUN_STATUS", default="UNKNOWN").upper()
    duration = float(env("RUN_DURATION_SEC", default="0"))
    rows = int(env("ROWS_PROCESSED", default="0"))
    criticality = env("PIPELINE_CRITICALITY", default="P4")
    team = env("PIPELINE_TEAM", default="unknown")
    failed = 1 if status not in ("SUCCESS", "SUCCEEDED") else 0
    now = int(time.time())

    dd_key = env("DD_API_KEY")
    dd_site = env("DD_SITE", default="datadoghq.com")
    dt_url = env("DYNATRACE_ENV_URL")
    dt_token = env("DYNATRACE_API_TOKEN")

    tags = [f"pipeline:{pipeline}", f"criticality:{criticality}",
            f"team:{team}", f"run_id:{run_id}"]

    failures = 0

    if dd_key:
        series = [
            {"metric": "databricks.pipeline.run.duration", "type": 0,
             "points": [{"timestamp": now, "value": duration}], "tags": tags},
            {"metric": "databricks.pipeline.run.failed", "type": 2,
             "points": [{"timestamp": now, "value": failed}], "tags": tags},
            {"metric": "databricks.pipeline.rows_processed", "type": 2,
             "points": [{"timestamp": now, "value": rows}], "tags": tags},
        ]
        code = send_datadog(dd_key, dd_site, series)
        print(f"emit-metrics: datadog -> {code}")
        if code not in (200, 202):
            failures += 1
    else:
        print("emit-metrics: DD_API_KEY unset, skipping Datadog")

    if dt_url and dt_token:
        dims = (f'pipeline="{pipeline}",criticality="{criticality}",'
                f'team="{team}",run_id="{run_id}"')
        lines = [
            f"databricks.pipeline.run.duration,{dims} {duration}",
            f"databricks.pipeline.run.failed,{dims} {failed}",
            f"databricks.pipeline.rows_processed,{dims} {rows}",
        ]
        code = send_dynatrace(dt_url, dt_token, lines)
        print(f"emit-metrics: dynatrace -> {code}")
        if code not in (200, 202, 204):
            failures += 1
    else:
        print("emit-metrics: DYNATRACE_ENV_URL/TOKEN unset, skipping Dynatrace")

    if failures:
        print("emit-metrics: one or more sinks failed", file=sys.stderr)
        sys.exit(1)
    print(f"emit-metrics: done pipeline={pipeline} status={status} failed={failed}")


if __name__ == "__main__":
    main()
