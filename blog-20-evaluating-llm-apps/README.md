# Evaluating LLM Apps: Stop Shipping on Vibes

"It looked good in the demo" is not a test strategy. In this post you'll learn how to build the eval harness that turns LLM quality into engineering: a versioned golden dataset of test cases, deterministic judges plus LLM judges that score outputs, and MLflow tracking every run. You'll see how to wire the harness into CI/CD as a quality gate — where a statistically meaningful regression blocks the PR — and the maintenance habits (calibration, dataset refresh, gaming watches) that keep the harness honest over time.

![Architecture diagram](./diagram.png)

The diagram shows the eval harness in CI/CD: a versioned golden dataset (150 real user questions from production logs, expected doc IDs per case, failure-mode coverage across adversarial/ambiguous/unanswerable cases) feeds `mlflow.evaluate()`, which runs the candidate app version through deterministic checks first (valid JSON, citations ⊆ retrieved, length) and then LLM judges (2–3 runs averaged, scoring groundedness and completeness 1–5). A quality gate compares scores against the main-branch baseline: pass merges and deploys, fail blocks the PR. Below, the CI/CD loop runs the harness on every PR (~20 minutes, scores logged to MLflow), and the maintenance panel keeps the harness honest — monthly judge calibration against humans, quarterly golden-set refresh, and a canary metric nobody optimizes for.

## Concepts covered

1. **Golden datasets.** The dataset *is* the harness: a versioned Delta table of 100–200 test cases, each with the input plus expected outputs or acceptance criteria. Sample cases from production logs (inference tables), cover failure modes — adversarial inputs, ambiguous questions, and "I don't know" as a correct output — and treat adding a new broken case as a commit, not a Slack message.
2. **Deterministic judges.** Fast, free, no LLM needed: is the output valid JSON? Do cited doc IDs exist in the retrieval set? Is the answer under the length limit? Run these first — they catch the dumb failures before you spend judge budget.
3. **LLM judges.** A strong model grades outputs against rubrics — groundedness (is every claim supported by retrieved docs?) and completeness (did it actually answer the question?). Noisy individually but reliable in aggregate; run each case 2–3 times and average, or judge variance will flake your gate.
4. **MLflow tracking for evals.** `mlflow.evaluate()` logs scores per test case, per metric, against the app version. This turns evals from a notebook you ran once into a system: quality over time, version A vs. B comparisons, and diffs of what changed.
5. **Quality gates in CI/CD.** The harness earns its keep as a gate, not a report: every PR that changes the prompt, retrieval config, or model version runs the golden set in CI, and a statistically meaningful regression vs. the main-branch baseline blocks the merge. Compare against the baseline — absolute thresholds are brittle against judge noise.
6. **Calibrate the judges.** Monthly, have a human grade ~30 cases alongside the LLM judge. If they disagree systematically, rewrite the rubric, not the scores. An uncalibrated judge is a random number generator with confidence.
7. **Refresh the golden set; watch for gaming.** Production drifts, so quarterly sample fresh traffic and retire stale cases — a frozen dataset slowly tests a product that no longer exists. And the moment a metric becomes a gate, someone optimizes for it: keep at least one metric nobody optimizes for (human spot-check satisfaction) as the canary.

## Hands-on exercises

Evals are a system you run, not a chapter you read. These three build HelpDesk Inc.'s harness at small scale on Free Edition: deterministic judges and MLflow tracking run fully free. Exercise 3 uses a rule-based judge stand-in — it marks the exact spot where a production LLM judge (served via Model Serving) would plug in.

1. **Build the golden dataset.** Synthesize 60 questions in three strata — 30 happy-path, 15 adversarial/ambiguous (including prompt-injection attempts), 15 unanswerable (no doc covers them, "I don't know" is correct) — each with question ID, category, expected doc IDs, and acceptance criteria; write it to Delta as a versioned table.
2. **Write the deterministic judges.** For a banking FAQ bot where compliance forbids markdown tables and caps responses at 400 words, implement three checks (cited docs ⊆ retrieved, ≤400 words, no markdown tables), plant exactly one violation of each on known question IDs, and log per-case pass/fail plus aggregate pass rates to MLflow.
3. **Calibrate the judge, then run the gate.** Hand-grade 10 cases and compare against the rule-based judge stand-in (agreement within ±1), simulate a baseline-vs-candidate embedding upgrade where the candidate improves adversarial cases but drops citations on happy-path ones, and apply the gate: ship only if candidate mean ≥ baseline mean − 0.1, with both means and the verdict logged to MLflow.

## Solutions

- `solution-1-the-golden-dataset.py` — Synthesizes the 60-question golden set across the three strata with IDs, categories, expected docs, and acceptance criteria, writes it to `evals.helpdesk_golden_v1`, and proves the category counts.
- `solution-2-deterministic-judges.py` — Implements the three deterministic judges, generates synthetic bot outputs with one planted violation per rule, scores all 60 cases, logs per-case and aggregate metrics to a single MLflow run, and asserts all planted violations (and only those) are caught.
- `solution-3-calibration-and-the-gate.py` — Computes judge agreement on 10 hand-graded cases, runs the baseline-vs-candidate comparison across the golden set, applies the ship/no-ship gate with the margin, and logs both means plus the verdict to MLflow.

## Prerequisites

- Databricks Free Edition — deterministic judges and MLflow tracking run fully free on serverless compute; all data is synthetic.
- Note: exercise 3 uses a rule-based judge stand-in in place of an LLM judge (which would need a Model Serving endpoint) — the calibration, baseline comparison, and logging around it are production-identical.
- Familiarity with MLflow tracking (blog 11); the HelpDesk example draws on inference-table logging from blog 17.
