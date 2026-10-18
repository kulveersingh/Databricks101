# Serve Open-Source LLMs Like APIs: Llama 3 on Databricks

Blog 17 of the Databricks series. A prototype on a hosted API works great until the math hits: 200 requests per second at per-token prices is a five-figure monthly line item that grows with usage — and every request ships customer data to a third party. This post covers the middle path: Databricks Model Serving with open-source models on provisioned throughput — an API endpoint, autoscaling, A/B testing, and inference-table logging, with the model, the GPUs, and the data all inside your cloud account.

![Architecture diagram](./diagram.png)

The diagram shows the Model Serving architecture end to end. Clients (web app, mobile, batch) hit an API gateway (auth, rate limits, OpenAI-compatible), which routes into the `pii-redaction-prod` serving endpoint running in your VPC: provisioned throughput (min 0, max 1200 units, scale-to-zero overnight) → GPU replicas (Llama 3 8B, optimized continuous batching) → A/B traffic split (v3 at 90%, v4 at 10%) → guardrails (input filter, length caps, output JSON validator). Model versions are served from the Unity Catalog model registry (rollback = point the endpoint at the previous version), and every request/response is logged to Delta inference tables that feed evals, fine-tuning data, and debugging. An "Operate it" panel covers latency/429 alerts, the GPU cost dashboard, and A/B quality comparison.

## Concepts covered

1. **Why open-source models, honestly.** Predictable cost at scale (provisioned GPUs instead of per-token markup), data that stays inside your VPC (customer text never crosses your account boundary — often the deciding factor for PII workloads), and control (swap models with a config change, fine-tune on your own data, no silent vendor checkpoints breaking prompts at 2am).
2. **Provisioned throughput vs. pay-per-token.** Pay-per-token: OpenAI-compatible endpoint, zero capacity planning, perfect for spiky or unpredictable traffic — but the most expensive per token at sustained volume. Provisioned: reserved GPU capacity you pay for whether traffic shows up or not — dramatically cheaper per request once utilization is healthy. You can switch between them without changing client code.
3. **What a serving endpoint actually is.** A single HTTPS URL with an OpenAI-compatible API; provisioned GPU replicas with vLLM-style continuous batching that autoscale between your min and max; model versions from Unity Catalog (rollback is "point at the previous version"); inference tables logging every request/response; and traffic splitting for A/B endpoints.
4. **The FormFlow example.** A PII-redaction API at 200 req/s: Llama 3 8B (right-sized — the 70B would be 4x the GPU cost), provisioned throughput with an overnight floor and 2x spike ceiling, guardrails (input filter, length cap, output validator against the redaction-spans schema, one retry, rules-based fallback), and inference tables partitioned by day for the future regression dataset.
5. **Best practices that actually matter.** Set the autoscaling floor (overnight cost) and ceiling (2x measured peak) deliberately and watch for 429s; run A/B endpoints for every model change instead of swapping 100% on a Friday; treat guardrails as part of the endpoint, not an afterthought; log everything to inference tables from day one; right-size the model — an 8B model routinely matches big ones on extraction/redaction.
6. **When this is the wrong call.** Spiky unpredictable traffic under ~10 req/s (idle GPUs cost you — use pay-per-token); a task that genuinely needs a frontier model where open-source fails your evals; or sub-50ms latency requirements (LLM inference is tens to hundreds of milliseconds — you need a different architecture).

## Hands-on exercises

1. **Harden the FormFlow PII-redaction client with guardrails.** Build the client from the post — input length cap, output validation against the redaction-spans schema, one retry, rules-based fallback — and test it against a mock endpoint that randomly returns malformed output.
2. **Run a 90/10 A/B test and read the inference table.** Route 90% of traffic to model v3 and 10% to v4 with a seeded router, log every request/response to a synthetic inference table, and compare the two versions side by side.
3. **Size provisioned throughput and price it against pay-per-token.** For 200 req/s at ~300ms per request: build the calculator, find how much provisioned throughput you need, determine the utilization crossover where it beats pay-per-token, and set the autoscaling floor and ceiling.

## Solutions

- `solution-1-guardrails-that-make-the-endpoint-produc.py` — Production-grade PII-redaction client (input length cap, schema validation of creative LLM JSON, one retry, rules-based fallback) tested against a mock flaky endpoint that randomly returns malformed output.
- `solution-2-the-a-b-router-and-inference-table.py` — Seeded 90/10 traffic router between model v3 and v4 writing every request/response to a synthetic inference table; compares quality and latency side by side for the deploy decision.
- `solution-3-the-throughput-sizing-calculator.py` — Sizing calculator for 200 req/s at ~300ms per request: computes required provisioned throughput, the pay-per-token crossover point, and autoscaling floor/ceiling recommendations.

## Prerequisites

- All three exercises run locally in pure Python against a mock endpoint and synthetic inference tables — no workspace, no GPU, no serving endpoint needed.
- Premium feature note: real traffic splitting, provisioned-throughput endpoints, and GPU-backed serving run on Databricks Premium tier with GPU compute; the router logic and sizing math here transfer directly.
