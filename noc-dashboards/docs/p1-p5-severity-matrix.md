# P1–P5 Severity Matrix — Databricks Pipelines

Business criticality is assigned by the pipeline owner at onboarding and stored as the
`criticality` tag on the Databricks job. It drives the Datadog monitor priority (1–5),
the Dynatrace alerting profile (P1/P2), and who the NOC engages. The NOC never
downgrades a severity without platform-team acknowledgement.

| Level | Definition | Example pipelines | NOC ack SLA | Engagement target | Engaged team | Channel |
|---|---|---|---|---|---|---|
| **P1** | Customer-facing or regulatory impact if delayed; money or compliance at risk | `fraud-detection` (real-time scoring), `ledger-bronze-silver-gold` (core ledger) | 15 min | Fix or workaround in 1 h | Platform team (primary), Tier 2 on bridge | Page (PagerDuty) + NOC bridge |
| **P2** | Material business impact within the day; SLA-bound downstream consumers | `aml-nightly-scoring` | 30 min | Fix in 4 h | Owning team (Risk), Platform team if infra | Page (PagerDuty), ticket auto-created |
| **P3** | Degraded analytics; no same-day customer impact | `risk-month-end-report` | 4 h | Next business day | Owning team (Risk) | Ticket, NOC monitors |
| **P4** | Internal/non-urgent aggregates | `marketing-aggregates` | 1 business day | Best effort | Owning team (CX) | Ticket only |
| **P5** | Informational (e.g. duration drift below SLO, not breaching) | any pipeline | — | — | — | Dashboard annotation only |

## Rules

1. **P1/P2 page; P3/P4 ticket; P5 is dashboard-only.** The Datadog monitors encode this:
   `datadog_monitor.pipeline_failure` sets `priority = 1..5` from criticality, and the
   message handle routes `@pagerduty-<team>` only for P1/P2.
2. **Duration SLOs are separate from failures.** A pipeline can succeed but breach its
   duration SLO (`datadog_monitor.pipeline_duration_slo`) — that fires at the same
   criticality but as a warning-class signal for P3 and below.
3. **Notify-no-data is on for scheduled pipelines.** If a scheduled run never starts,
   the monitor fires — a missing run is as bad as a failed one for P1/P2.
4. **Escalation path on failure**: NOC acknowledges → checks the runbook link in the
   alert (deep link to the Databricks job run, last successful run, recent changes) →
   first 15 minutes of triage per the pipeline runbook → if infra/root-cause unclear,
   engage Platform team; if data/logic, engage Tier 2 of the owning team.
5. **Severity review quarterly.** P3s that page-adjacent twice get promoted; P1s that
   never fire get questioned. Alert fatigue is a P1 risk of its own.
