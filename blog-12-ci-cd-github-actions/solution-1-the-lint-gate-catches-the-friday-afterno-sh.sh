# Blog 12 — CI/CD for Data Pipelines with GitHub Actions
# Exercise 1: The lint gate catches the Friday-afternoon edit
# Requires: Everything here runs locally — a repo directory, `ruff`/`pytest`, and YAML files. No workspace needed.

pip install ruff
ruff check src/ tests/
