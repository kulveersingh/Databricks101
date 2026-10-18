# Blog 11 — Databricks Asset Bundles: Infrastructure as Code Done Right
# Exercise 3: Generate a bundle from a hand-built job
# Requires: All three exercises run locally — a project directory, YAML files, and a Python checker. No workspace needed.

import json, yaml
from pathlib import Path

# sample hand-built job, as exported from the UI / Jobs API
hand_built = {
    "name": "nightly-returns",
    "schedule": {"quartz_cron_expression": "0 0 2 * * ?", "timezone_id": "America/New_York"},
    "tasks": [
        {"task_key": "run_returns",
         "notebook_task": {"notebook_path": "/Users/priya/returns_pipeline",
                            "base_parameters": {"catalog": "prod_catalog"}}}
    ],
    "notifications": {"on_failure": ["data-oncall@loopcart.example"]},
}

resource = {"resources": {"jobs": {"nightly_returns": {
    "name": "[${bundle.target}] " + hand_built["name"],
    "tasks": [
        {"task_key": t["task_key"],
         "notebook_task": {
             "notebook_path": "./src/returns_pipeline.py",  # code now lives in Git
             "base_parameters": t["notebook_task"].get("base_parameters", {}),
         }}
        for t in hand_built["tasks"]
    ],
    "schedule": hand_built["schedule"],
    "notifications": hand_built.get("notifications", {}),
}}}}

out = Path("returns_bundle/resources/nightly_returns.job.yml")
out.write_text(yaml.safe_dump(resource, sort_keys=False))
print(f"wrote {out}")
