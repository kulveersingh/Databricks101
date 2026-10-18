# Blog 17 — Serve Open-Source LLMs Like APIs: Llama 3 on Databricks
# Exercise 3: the throughput sizing calculator.
# Requires: Databricks Free Edition for client, guardrail, and router logic. Real provisioned-throughput serving needs Premium + GPU; pay-per-token is the Free Edition path.

REQ_PER_SEC = 200
LATENCY_SEC = 0.30
PROVISIONED_MONTHLY_PER_UNIT = 1.0   # normalized cost units
PAY_PER_TOKEN_PER_1K_REQ = 0.06      # normalized: ~$0.06 per 1k requests

in_flight = REQ_PER_SEC * LATENCY_SEC            # Little's law
ceiling = in_flight * 2                          # 2x headroom for spikes
floor = in_flight * 0.25                         # overnight minimum

print(f"in-flight={in_flight:.0f} floor={floor:.0f} ceiling={ceiling:.0f} throughput units")

monthly_requests = REQ_PER_SEC * 3600 * 24 * 30
for util in (0.30, 0.60, 1.00):
    provisioned = ceiling * PROVISIONED_MONTHLY_PER_UNIT
    payg = monthly_requests * util * PAY_PER_TOKEN_PER_1K_REQ / 1000
    winner = "provisioned" if provisioned < payg else "pay-per-token"
    print(f"util={util:.0%}: provisioned={provisioned:.0f} pay-per-token={payg:.0f} -> {winner}")

assert ceiling == 120  # sanity check: 60 in flight x 2x headroom
