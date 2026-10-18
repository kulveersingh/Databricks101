# Blog 11 — Databricks Asset Bundles: Infrastructure as Code Done Right
# Exercise 1: Bundle-ify Priya's returns pipeline
# Requires: All three exercises run locally — a project directory, YAML files, and a Python checker. No workspace needed.

def main():
    # returns analysis: read bronze returns, aggregate reason codes, write gold
    print("returns pipeline: bronze -> silver -> gold")

if __name__ == "__main__":
    main()
# --- next cell ---

import sys, yaml
from pathlib import Path

root = Path("returns_bundle")
errors = []

def fail(msg):
    errors.append(msg)

cfg = yaml.safe_load((root / "databricks.yml").read_text())
targets = cfg.get("targets", {})
if not targets:
    fail("no targets defined")

for name, t in targets.items():
    if not t.get("workspace", {}).get("host"):
        fail(f"target '{name}': missing workspace.host")

# every notebook_path referenced by a resource must exist on disk
for res_file in (root / "resources").glob("*.yml"):
    res = yaml.safe_load(res_file.read_text())
    for job_name, job in res.get("resources", {}).get("jobs", {}).items():
        for task in job.get("tasks", []):
            nb = task.get("notebook_task", {}).get("notebook_path")
            if nb and not (root / nb.lstrip("./")).exists():
                fail(f"job '{job_name}': notebook_path '{nb}' not found")

# resolved names per target: dev gets the prefix, prod stays clean
for name, t in targets.items():
    prefix = "[dev priya] " if t.get("mode") == "development" and name == "dev" else f"[{name}] "
    clean = "" if (t.get("mode") == "production" and name == "prod") else prefix
    print(f"target={name:8s} resolved job name: '{clean}nightly-returns'")

if errors:
    print("VALIDATION FAILED:")
    print("\n".join(f"  - {e}" for e in errors))
    sys.exit(1)
print("VALIDATION PASSED")
