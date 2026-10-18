# Blog 20 — Evaluating LLM Apps: Stop Shipping on Vibes
# Exercise 3: calibration and the gate.
# Requires: Evals are a system you run, not a chapter you read. These three exercises build HelpDesk Inc.'s harness at small scale on Free Edition: deterministic judges and MLflow tracking run fully free. Exercis

import mlflow
import numpy as np

# rule-based judge stand-in: groundedness 1-5 from checkable signals.
# In production this is where the LLM judge call goes; the harness around it
# (calibration, baseline comparison, MLflow logging) stays identical.
def judge_standin(question, answer, expected_docs):
    if not expected_docs:
        return 5 if "don't know" in answer.lower() else 1  # abstention is correct here
    return 4 if any(d in answer for d in expected_docs) else 2

# 1. calibrate on 10 hand-graded cases — replace these grades with YOURS
sample = spark.table("evals.helpdesk_golden_v1").limit(10).collect()
hand_grades = [5, 4, 5, 3, 5, 4, 2, 5, 4, 5]
auto = []
for r in sample:
    docs = r["expected_docs"].split(",") if r["expected_docs"] else []
    ans = f"Per {docs[0]}: {r['acceptance']}" if docs else "I don't know"
    auto.append(judge_standin(r["question"], ans, docs))
agree = sum(abs(h - a) <= 1 for h, a in zip(hand_grades, auto)) / len(hand_grades)
print(f"judge agreement (within ±1): {agree:.0%}")

# 2. baseline vs candidate across the golden set
golden = spark.table("evals.helpdesk_golden_v1").collect()

def baseline_answer(r):
    docs = r["expected_docs"].split(",") if r["expected_docs"] else []
    return f"Per {docs[0]}: {r['acceptance']}" if docs else "I don't know"

def candidate_answer(r):  # better on adversarial, drops citations on happy-path
    docs = r["expected_docs"].split(",") if r["expected_docs"] else []
    if r["category"] == "adversarial":
        return f"Per {docs[0]}: {r['acceptance']} (extra retrieved context considered)"
    if r["category"] == "happy":
        return "Here's the short version."
    return baseline_answer(r)

def mean_score(answer_fn):
    return float(np.mean([
        judge_standin(r["question"], answer_fn(r),
                      r["expected_docs"].split(",") if r["expected_docs"] else [])
        for r in golden]))

mlflow.set_experiment("/helpdesk/eval-harness")
with mlflow.start_run(run_name="embedding-upgrade-gate"):
    b, c = mean_score(baseline_answer), mean_score(candidate_answer)
    margin = c - b
    verdict = "SHIP" if margin >= -0.1 else "NO-SHIP"
    mlflow.log_metric("baseline_mean", b)
    mlflow.log_metric("candidate_mean", c)
    mlflow.log_param("verdict", verdict)
    print(f"baseline={b:.2f} candidate={c:.2f} margin={margin:+.2f} → {verdict}")
    print("Like the post's bge-large call: a global upgrade that regresses the common "
          "cases ships nowhere — or ships behind a router, not globally.")
