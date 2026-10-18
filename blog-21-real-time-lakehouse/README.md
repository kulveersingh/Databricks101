# The Real-Time Lakehouse: Kafka to Sub-100ms Serving

Batch was fine until the business wanted prices that react to demand *now*. In this post you'll learn the full real-time chain — Kafka → Delta Live Tables → Feature Store (online) → Model Serving — through a personalized pricing engine that reacts to live demand in ~65ms end-to-end. You'll see why exactly-once semantics and backpressure handling are the two guarantees that matter, how the online feature store eliminates training/serving skew, and what four dashboards to watch at 3 AM when something breaks.

![Architecture diagram](./diagram.png)

The diagram shows the end-to-end chain for ShopLine's personalized pricing engine: Kafka ingests ~50k events/sec (views, cart adds, purchases, inventory updates) as a durable, replayable log that buffers 8x flash-sale bursts; Delta Live Tables processes it exactly-once — bronze raw events, silver validated (expectations reject bad rows), gold 15-minute demand velocity — with checkpoints and autoscaling; the Feature Store serves fresh state with ~8ms online lookups (same feature definitions for training and serving, so no skew); and Model Serving scores the price multiplier with a business-rule clamp (±15%, never below cost), landing at ~65ms p99 against a 100ms budget. Below the chain: the two guarantees (exactly-once via Kafka offsets in DLT checkpoints plus idempotent Delta writes; backpressure via consumer-lag alerts and DLT autoscaling) and the four operate-it signals — Kafka consumer lag, freshness SLO, online store health, and serving vitals — on one dashboard.

## Concepts covered

1. **The chain, link by link.** Real-time isn't one feature — it's Kafka (durable, replayable ingest), DLT (declarative bronze→silver→gold with checkpoints and retries), Feature Store online store (millisecond feature lookups), and Model Serving (sub-100ms decisions). Break any link and you're back to a five-minute cron with better marketing.
2. **Exactly-once processing.** A Kafka redelivery after a consumer restart must never double-count a purchase or double-charge a feature aggregate. You get it from Kafka offsets tracked in DLT checkpoints plus Delta's idempotent writes — and you test it honestly by killing a streaming cluster mid-run and verifying the silver table, not just the restart.
3. **Backpressure.** When a flash sale 10x's your event rate, downstream can't keep up — without defenses you get OOM crashes and cascading failures. The defenses: Kafka consumer-lag alerting as early warning, DLT autoscaling as lag grows, and trigger-interval tuning for small micro-batches. Design for 5–10x bursts; hope for 2x.
4. **The Feature Store online/offline split.** The link most architectures fumble: DLT writes feature values to Delta (the offline truth for training), and they're published to a low-latency online store for serving. Same feature definitions for training and serving — no training/serving skew, the silent killer of real-time ML.
5. **The latency budget.** Sub-100ms means every millisecond is accounted for: ~10ms network, ~8ms feature lookup, ~30–60ms inference, with headroom. That's the budget that makes "real-time" real — and the reason the pricing model is a gradient-boosted model, not an LLM (right tool for the job).
6. **The model proposes, rules dispose.** No ML model gets unbounded pricing authority. A business-rule clamp (±15% from list, never below cost) sits on top of the model — that's the guardrail that lets the business trust the system. Every decision is logged to a Delta table so it can be replayed and explained.
7. **Operating it: four signals, one dashboard.** Kafka consumer lag (alert on sustained growth, not absolute values), end-to-end freshness SLO ("features never more than 5 minutes stale," measured continuously), online store health (hit rate, lookup p99, offline→online lag), and serving endpoint vitals (request rate, inference p99, errors, 429s). At 3 AM the on-call engineer sees the whole chain in ten seconds.
8. **Decide what degrades, before it degrades.** When a flash sale 8x's traffic, freshness is allowed to lag by a minute or two — a tradeoff the business accepted in advance. Designing which SLO bends and which must not is the difference between an incident and a plan.

## Hands-on exercises

Streaming is the one part of this post you can genuinely rehearse on Free Edition — Structured Streaming runs on serverless compute. Delta Live Tables is the premium piece, so these exercises use plain `readStream` / `writeStream` with manual checks standing in for DLT expectations; the semantics (watermarks, dedupe, idempotent sinks) are the identical ones DLT manages for you.

1. **Build ShopLine's demand-velocity stream.** Use the `rate` source as a Kafka stand-in producing synthetic events (2% malformed), build bronze → silver with a 10-minute watermark, `dropDuplicates` on `event_id`, and quarantine malformed events (visible, counted — never silently dropped); then compute gold 15-minute per-product demand velocity and prove zero malformed rows reached silver.
2. **Prove exactly-once under redelivery.** Simulate a Kafka consumer restart by unioning the source with itself, absorb redelivery with a watermark plus `dropDuplicates`, and sink via `foreachBatch` MERGE keyed on `event_id` so the write itself is idempotent — then assert `COUNT(*) = COUNT(DISTINCT event_id)` and confirm both numbers hold after restarting on the same checkpoint.
3. **Survive the burst, measure what degrades.** Run the stream at 100 rows/sec, ramp to 500 rows/sec, and measure per-phase freshness (max event-time → processing-time lag). Decide in advance, in writing: freshness may degrade, correctness may not — then verify lag grows while counts stay exact.

## Solutions

- `solution-1-the-demand-velocity-stream.py` — Builds the rate-source event stream with injected malformed events, bronze → silver with watermark/dedupe/quarantine, and gold demand-velocity windows to memory sinks, asserting silver is clean.
- `solution-2-exactly-once-under-redelivery.py` — Duplicates every event via self-union, dedupes with a watermark, and sinks with an idempotent MERGE on `event_id` keyed off a Unity Catalog Volume checkpoint, proving exactly-once after restart.
- `solution-3-burst-and-the-freshness-slo.py` — Runs normal and burst phases with availableNow triggers, records per-phase row counts and max event-time lag, and prints the written degrade decision: lag grew, counts stayed exact.

## Prerequisites

- Databricks Free Edition — Structured Streaming runs on serverless compute; the `rate` source stands in for Kafka and all data is synthetic.
- Note: Delta Live Tables is a premium feature, so the exercises use plain `readStream` / `writeStream` with manual checks where DLT expectations would sit declaratively — the semantics are identical.
- Familiarity with Structured Streaming basics (blog 6); the serving endpoint and 429 concepts draw on blog 17.
