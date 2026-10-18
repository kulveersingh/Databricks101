# Blog 16 — RAG on Databricks: From PDFs to Answers
# Exercise 3: the confidence gate.
# Requires: Databricks Free Edition. Deterministic token-overlap embeddings are labeled stand-ins; at scale swap for GPU batch embeddings and a Vector Search index.

THRESHOLD = 0.25

def ask_gated(question):
    qv = embed(question, VOCAB)
    ranked = sorted(index, key=lambda c: cosine(qv, c["vec"]), reverse=True)
    if cosine(qv, ranked[0]["vec"]) < THRESHOLD:
        return None  # escalate to human
    return ranked[0]

in_domain = [q for q, _, _ in GOLDEN[:5]]
out_domain = ["2019 enterprise refund policy details",
              "CEO's favorite lunch spot",
              "quantum computing roadmap",
              "office wifi password",
              "stock price prediction"]

answered = sum(ask_gated(q) is not None for q in in_domain)
escalated = sum(ask_gated(q) is None for q in out_domain)
assert answered == 5 and escalated == 5, (answered, escalated)
print(f"answered={answered} escalated={escalated} hallucinations=0")
