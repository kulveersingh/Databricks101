# Blog 11 — Databricks Asset Bundles: Infrastructure as Code Done Right
# Exercise 2: Per-target variables
# Requires: All three exercises run locally — a project directory, YAML files, and a Python checker. No workspace needed.

import re

var_pattern = re.compile(r"\$\{var\.([a-z_]+)\}")
declared = set(cfg.get("variables", {}))

def resolve(value, target_vars, target_name, context):
    def repl(m):
        var = m.group(1)
        if var not in declared:
            fail(f"{context}: variable '{var}' is not declared in 'variables'")
        if var not in target_vars:
            fail(f"{context}: target '{target_name}' does not set variable '{var}'")
        return str(target_vars.get(var, ""))
    return var_pattern.sub(repl, value) if isinstance(value, str) else value

for name, t in targets.items():
    tvars = t.get("variables", {})
    resolved_catalog = resolve("${var.catalog}", tvars, name, f"target '{name}'")
    resolved_email = resolve("${var.alert_email}", tvars, name, f"target '{name}'")
    print(f"target={name:8s} catalog={resolved_catalog:16s} alerts={resolved_email}")

# demonstrate the failure: point notifications at ${var.pager_duty} and re-run
