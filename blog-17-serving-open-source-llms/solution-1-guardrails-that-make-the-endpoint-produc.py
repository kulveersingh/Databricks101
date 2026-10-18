# Blog 17 — Serve Open-Source LLMs Like APIs: Llama 3 on Databricks
# Exercise 1: guardrails that make the endpoint production-safe.
# Requires: Databricks Free Edition for client, guardrail, and router logic. Real provisioned-throughput serving needs Premium + GPU; pay-per-token is the Free Edition path.

import json, random, re

rnd = random.Random(7)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"\b\d{3}[-.]\d{3}[-.]\d{4}\b")

def mock_endpoint(text):
    """Simulates a flaky LLM endpoint: valid JSON / malformed / timeout."""
    r = rnd.random()
    if r < 0.10: raise TimeoutError("endpoint timeout")
    spans = [{"start": m.start(), "end": m.end(), "type": "EMAIL"}
             for m in EMAIL.finditer(text)]
    spans += [{"start": m.start(), "end": m.end(), "type": "PHONE"}
              for m in PHONE.finditer(text)]
    if r < 0.20: return "{not valid json"          # malformed
    return json.dumps({"redactions": spans})

def rules_based_redact(text):
    spans = [{"start": m.start(), "end": m.end(), "type": "EMAIL"}
             for m in EMAIL.finditer(text)]
    spans += [{"start": m.start(), "end": m.end(), "type": "PHONE"}
              for m in PHONE.finditer(text)]
    return {"redactions": spans, "fallback": True}

MAX_INPUT_CHARS = 4000

def valid_output(obj):
    return (isinstance(obj, dict) and isinstance(obj.get("redactions"), list)
            and all({"start", "end", "type"} <= set(s) for s in obj["redactions"]))

def redact(text):
    if len(text) > MAX_INPUT_CHARS:
        raise ValueError("input exceeds length cap")   # cost control
    for _ in range(2):                                  # one retry
        try:
            out = json.loads(mock_endpoint(text))
            if valid_output(out): return out
        except (TimeoutError, json.JSONDecodeError):
            continue
    return rules_based_redact(text)                     # fallback, always valid

results, fallbacks = [], 0
for i in range(200):
    text = f"contact user{i}@example.com or 555-01{i:04d} for form {i}"
    out = redact(text)
    assert valid_output(out), f"invalid output leaked downstream: {out}"
    results.append(out)
    fallbacks += out.get("fallback", False)

print(f"downstream-valid: {len(results)}/200 | fallbacks: {fallbacks}")
assert len(results) == 200 and fallbacks > 0
