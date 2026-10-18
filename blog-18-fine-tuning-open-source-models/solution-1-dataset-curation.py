# Blog 18 — Fine-Tune Mistral on Your Own Data: SFT, LoRA, and MLflow
# Exercise 1: dataset curation.
# Requires: Before you spend a dollar on GPU time, run the loop small. These three exercises stay on Free Edition's CPU-only serverless compute — no model downloads, all data generated in the notebook — and cover

import hashlib, json
import mlflow
import numpy as np

rng = np.random.default_rng(42)

CATEGORIES = ["billing", "access", "bug"]
POLICY = {"billing": "credit-5-days", "access": "sso-reset", "bug": "sla-99-9"}

def make_pair(i, cat):
    n = rng.integers(1000, 9999)
    customer = f"Ticket {n}: my {cat} issue started yesterday, please help — ref {i}"
    response = (f"Thanks for reaching out. For this {cat} case we've applied policy "
                f"{POLICY[cat]}; here's what happens next: our team follows up "
                f"within one business day.")
    return {"customer": customer, "response": response, "category": cat}

pairs = [make_pair(i, CATEGORIES[i % 3]) for i in range(270)]
pairs += [dict(pairs[i]) for i in rng.choice(270, 24, replace=False)]  # near-duplicates
pairs += [{"customer": "thanks!", "response": "You're welcome!", "category": "billing"}
          for _ in range(6)]                                            # one-liners
rng.shuffle(pairs)
n_generated = len(pairs)

# 1. dedupe on normalized customer text
seen, deduped = set(), []
for p in pairs:
    key = p["customer"].strip().lower()
    if key not in seen:
        seen.add(key)
        deduped.append(p)

# 2. drop one-liners / thin responses
filtered = [p for p in deduped
            if len(p["customer"].split()) > 3 and len(p["response"].split()) >= 10]

# 3. stratified 80/20 split
train, heldout = [], []
for cat in CATEGORIES:
    bucket = [p for p in filtered if p["category"] == cat]
    cut = int(len(bucket) * 0.8)
    train += bucket[:cut]
    heldout += bucket[cut:]

# 4. dataset hash = the dataset version
digest = hashlib.sha256(
    json.dumps(sorted(p["customer"] for p in train)).encode()).hexdigest()[:16]

# 5. prove no leakage into the heldout set
overlap = set(p["customer"] for p in train) & set(p["customer"] for p in heldout)

mlflow.set_experiment("/ticketwise/data-curation")
with mlflow.start_run(run_name="ticketwise-data-v1"):
    mlflow.log_param("n_generated", n_generated)
    mlflow.log_param("n_deduped", len(deduped))
    mlflow.log_param("n_filtered", len(filtered))
    mlflow.log_param("n_train", len(train))
    mlflow.log_param("n_heldout", len(heldout))
    mlflow.log_param("dataset_sha16", digest)
    mlflow.log_metric("leakage_overlap", len(overlap))

print(f"generated={n_generated} deduped={len(deduped)} filtered={len(filtered)} "
      f"train={len(train)} heldout={len(heldout)} overlap={len(overlap)} hash={digest}")
