# Blog 18 — Fine-Tune Mistral on Your Own Data: SFT, LoRA, and MLflow
# Exercise 3: the eval gate.
# Requires: Before you spend a dollar on GPU time, run the loop small. These three exercises stay on Free Edition's CPU-only serverless compute — no model downloads, all data generated in the notebook — and cover

import mlflow
import numpy as np

POLICY = {0: "credit-5-days", 1: "sso-reset", 2: "sla-99-9"}

def base_draft(ticket):
    return ("Thanks for contacting support. We understand your concern and our team "
            "is looking into this matter. We appreciate your patience and will update you soon.")

def finetuned_draft(ticket):
    kw = POLICY[ticket["cat"]]
    return (f"Thanks for reaching out. Per policy {kw}, here's what happens next: "
            f"we've applied the fix for ticket {ticket['id']} and you'll see it "
            f"reflected within the stated window. Let us know if anything looks off.")

def judge(draft, keyword):
    if len(draft.split()) < 20:
        return 0
    return (1 if keyword in draft else 0) + (1 if "here's what happens next" in draft else 0)

tickets = [{"id": i, "cat": i % 3} for i in range(40)]
base_scores = [judge(base_draft(t), POLICY[t["cat"]]) for t in tickets]
ft_scores = [judge(finetuned_draft(t), POLICY[t["cat"]]) for t in tickets]

mlflow.set_experiment("/ticketwise/eval-gate")
with mlflow.start_run(run_name="v1-gate"):
    mlflow.log_metric("base_mean", float(np.mean(base_scores)))
    mlflow.log_metric("finetuned_mean", float(np.mean(ft_scores)))
    mlflow.log_param("n_heldout", len(tickets))

margin = float(np.mean(ft_scores) - np.mean(base_scores))
print(f"base={np.mean(base_scores):.2f} finetuned={np.mean(ft_scores):.2f} margin={margin:+.2f}")
print("DECISION:", "SHIP v1" if margin >= 0.5 else "NO-SHIP — margin within noise, back to the data")
