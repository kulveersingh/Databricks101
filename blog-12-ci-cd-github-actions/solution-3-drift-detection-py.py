# Blog 12 — CI/CD for Data Pipelines with GitHub Actions
# Exercise 3: Drift detection
# Requires: Everything here runs locally — a repo directory, `ruff`/`pytest`, and YAML files. No workspace needed.

import json, sys, yaml

def flatten(obj, prefix=""):
    flat = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            flat.update(flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            flat.update(flatten(v, f"{prefix}[{i}]"))
    else:
        flat[prefix] = obj
    return flat

desired = yaml.safe_load(open("resources/orders.job.yml"))["resources"]["jobs"]["orders_dlt"]
live = json.load(open("live_snapshot.json"))

d, l = flatten(desired), flatten(live)
drifted = []
for key in sorted(set(d) | set(l)):
    if d.get(key) != l.get(key):
        drifted.append((key, d.get(key, "<absent>"), l.get(key, "<absent>")))

if drifted:
    print("DRIFT DETECTED:")
    for key, want, got in drifted:
        print(f"  {key}: desired={want!r} live={got!r}")
    sys.exit(1)
print("NO DRIFT: live matches desired state")
