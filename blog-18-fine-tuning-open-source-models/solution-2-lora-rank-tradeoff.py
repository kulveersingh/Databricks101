# Blog 18 — Fine-Tune Mistral on Your Own Data: SFT, LoRA, and MLflow
# Exercise 2: LoRA rank tradeoff.
# Requires: Before you spend a dollar on GPU time, run the loop small. These three exercises stay on Free Edition's CPU-only serverless compute — no model downloads, all data generated in the notebook — and cover

import numpy as np

rng = np.random.default_rng(7)
m = n = 512

# structured update: 8 strong latent components + noise (like a real task update)
U0 = rng.standard_normal((m, 8)); V0 = rng.standard_normal((n, 8))
dW_structured = (U0 @ V0.T) / 8 + 0.05 * rng.standard_normal((m, n))
dW_noise = rng.standard_normal((m, n))

def rank_report(dW, ranks=(4, 16)):
    U, S, Vt = np.linalg.svd(dW, full_matrices=False)
    frob = np.linalg.norm(dW)
    for r in ranks:
        approx = (U[:, :r] * S[:r]) @ Vt[:r, :]
        err = np.linalg.norm(dW - approx) / frob
        pct = 100 * r * (m + n) / (m * n)
        print(f"  rank {r:2d}: {pct:5.2f}% of params, relative error {err:.3f}")

print("structured ΔW (task-like):")
rank_report(dW_structured)
print("pure-noise ΔW:")
rank_report(dW_noise)
