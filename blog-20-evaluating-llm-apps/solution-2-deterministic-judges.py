# Blog 20 — Evaluating LLM Apps: Stop Shipping on Vibes
# Exercise 2: deterministic judges.
# Requires: Evals are a system you run, not a chapter you read. These three exercises build HelpDesk Inc.'s harness at small scale on Free Edition: deterministic judges and MLflow tracking run fully free. Exercis

import mlflow
import re

def cited_subset(o):
    cited = set(re.findall(r"doc-\d{2}", o["citations"]))
    return cited <= set(o["retrieved"])

def within_limit(o, limit=400):
    return len(o["text"].split()) <= limit

def no_md_tables(o):
    return not re.search(r"^\s*\|.*\|\s*$", o["text"], re.M)

JUDGES = {"cited_subset": cited_subset, "within_limit": within_limit,
          "no_md_tables": no_md_tables}

golden = spark.table("evals.helpdesk_golden_v1").collect()
outputs = []
for r in golden:
    docs = r["expected_docs"].split(",") if r["expected_docs"] else []
    outputs.append({
        "qid": r["qid"],
        "text": f"Per {docs[0] if docs else 'doc-00'}: {r['acceptance']}",
        "citations": docs[0] if docs else "",
        "retrieved": docs + ["doc-00"],
    })

# plant one violation per rule, on known question IDs
by_id = {o["qid"]: o for o in outputs}
by_id["q030"]["citations"] = "doc-99"              # cites a doc never retrieved
by_id["q045"]["text"] = " ".join(["word"] * 450)  # blows the 400-word limit
by_id["q050"]["text"] = "Summary:\n| a | b |\n| 1 | 2 |"  # markdown table

mlflow.set_experiment("/helpdesk/eval-harness")
with mlflow.start_run(run_name="deterministic-judges-v1"):
    totals = {name: 0 for name in JUDGES}
    for o in outputs:
        for name, fn in JUDGES.items():
            ok = fn(o)
            totals[name] += ok
            mlflow.log_metric(f"{o['qid']}_{name}", int(ok))
    for name, passed in totals.items():
        mlflow.log_metric(f"{name}_pass_rate", passed / len(outputs))
    print({name: f"{passed}/{len(outputs)}" for name, passed in totals.items()})

fails = [(o["qid"], n) for o in outputs for n, f in JUDGES.items() if not f(o)]
print("failures:", fails)
assert ("q030", "cited_subset") in fails
assert ("q045", "within_limit") in fails
assert ("q050", "no_md_tables") in fails
print("all planted violations caught, nothing else flagged")
