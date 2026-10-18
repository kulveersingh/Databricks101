# Workflows: Replacing Your Cron Jobs for Good

Blog 10 of the Databricks series. You will learn why cron was never designed to run data pipelines — no dependencies, no retries, no visibility, no alerting — and how Databricks Workflows closes all four gaps: explicit task DAGs with quality gates, per-task retries and timeouts, alerts that reach you, run history with repair-from-failure, and job clusters that keep production compute cheap.

![Architecture diagram](./diagram.png)

The diagram shows LendLoop's nightly ML feature refresh as a Workflows job: `ingest` (with 3 retries for the flaky bureau API) → `validate` (quality gate that stops bad data) → `build_features` → `train` (weekly retrain) → `evaluate` (metrics gate that must pass) → `publish` (with a hard 6:00 AM SLA). Two callouts cover failure handling — repair the run and resume from the failed task instead of hand-written "resume from step N" scripts — and alerting — Slack/email/PagerDuty on failure or SLA miss, paging at 5:30 AM if the run isn't green. The bottom panel makes the cost decision explicit: job clusters (spun up per run, terminated after — pay for 40 minutes, not 24 hours) vs. all-purpose clusters for dev only (24/7 for a 40-minute job is a money fire).

## Concepts covered

1. **Why cron breaks down.** Cron was designed in the 1970s to run commands on a schedule, not data pipelines. It has no dependencies (faked with sleep timers), no retries (a transient failure is a total failure), no visibility (did it run? check the log file on the VM), and no alerting (cron emails root, and nobody reads root's mail) — every gap becomes a page or a silent data-quality incident.
2. **Jobs, tasks, and dependencies.** A Databricks Job is a DAG of tasks — notebooks, JARs, Python files, SQL, DLT pipelines — with explicit `depends_on` edges, so if `ingest` takes 3 hours instead of 30 minutes, downstream just waits. You can branch conditionally (run `deploy` only if `evaluate` passes its gate) and fan out parallel tasks; the DAG is the documentation.
3. **Retries, timeouts, and alerts that actually reach you.** Automatic per-task retries with backoff turn a transient S3 timeout into a 5-minute retry instead of a page. Per-task timeouts kill stuck tasks instead of letting them burn money silently. Notifications fire on start, success, failure, and SLA miss — to email, Slack, PagerDuty, or webhooks.
4. **Run history and repair.** Every run is recorded with per-task status, duration, and logs. When a run fails at task 4 of 6, you fix the issue and *repair the run* — it resumes from the failed task instead of rerunning the first three. Repair alone replaces an entire category of hand-written resume scripts.
5. **Job clusters vs. all-purpose clusters: the cost decision.** Production jobs run on job clusters — spun up when the job starts, terminated when it ends, so you pay only for the run. All-purpose clusters left running 24/7 for a 40-minute nightly job is the single most common Databricks cost waste. (One nuance: job clusters have startup time, so extremely tight, every-15-minute SLAs may justify a small always-on cluster or serverless.)
6. **When to graduate beyond Workflows.** If your pipeline spans Databricks, dbt Cloud, Snowflake, and Kubernetes, a neutral orchestrator like Airflow coordinating everything is cleaner; complex event-driven routing belongs with the streaming primitives from post #6; and real human-in-the-loop approval workflows (pause, notify, wait, resume) belong in a dedicated orchestrator.

## Hands-on exercises

1. **Nightly feature refresh with an SLA** — Implement a mini workflow engine in Python (tasks with `depends_on`, `max_retries` with backoff, per-task `timeout`, SLA deadline check), model LendLoop's six-task pipeline with a flaky bureau API inside `ingest`, and read the run log to see dependency ordering, retries, and an explicit SLA-miss line on the slow run.
2. **Repair from the failed task** — Extend the engine with persisted per-task status and a `repair()` that resumes from the first failed task, then seed a failure at `evaluate`, fix the threshold, and repair — proving the successful tail is skipped.
3. **Conditional publish gate** — Extend the engine with task outputs and conditional edges so `publish` runs only if `evaluate`'s metric clears its threshold; run twice (passing and failing) and confirm the failing run halts after `evaluate` with a "gate blocked" line.

## Solutions

- `solution-1-nightly-feature-refresh-with-an-sla.py` — The mini workflow engine (`Task`, `Workflow` with retries, timeouts, backoff, SLA deadline) plus the LendLoop six-task pipeline definition with the flaky bureau API.
- `solution-2-repair-from-the-failed-task.py` — Extends the engine with persisted task status and `repair()`, demonstrating resume-from-failed-task on a seeded `evaluate` failure.
- `solution-3-conditional-publish-gate.py` — Extends the engine with task outputs and conditional edges, showing `publish` executing only when the evaluation metric passes its gate.

## Prerequisites

All three exercises run locally in plain Python — no workspace, no cluster, no cron daemon. **Tier note:** the full Jobs API surface these exercises mirror isn't exercisable from a bare checkout, so we simulate Workflows semantics — DAG dependencies, retries with backoff, per-task timeouts, SLA alerts, run history, and repair — with a small local engine. The semantics are the lesson; the UI is just buttons.

> Companion post: `blog-10-workflows-orchestration.md` in the Databricks blog series.
