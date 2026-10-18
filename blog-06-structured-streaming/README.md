# Structured Streaming in Production: Beyond the Tutorial

The tutorial version of Structured Streaming is fifteen lines; the production version is a different discipline. This post covers the three concepts that separate a demo stream from a pipeline you can bet the company on: **watermarks** (how you handle lateness), **exactly-once** (how you survive restarts), and **foreachBatch** (how you do real work — merges, model scoring — inside a stream), plus the three metrics every streaming dashboard should have.

![Architecture diagram](./diagram.png)

The diagram shows the SwiftPay real-time fraud pipeline: Kafka authorizations keyed by transaction ID flow into a features stream (10-minute watermark on event time, windowed aggregation into a state store, card-velocity features), then `foreachBatch` scores with the fraud model and `MERGE`s into the `account_risk` gold Delta table — idempotent on `batch_id` — which the Auth API reads (~40s swipe-to-decision). Late events and future timestamps route to a quarantine table with arrival metadata, guarded by a sanity filter rejecting `event_ts` more than an hour in the future. Underneath everything sits checkpoint storage on durable, separate storage — offsets and state committed transactionally with each micro-batch. The footer names the three health metrics: watermark age, late-drop rate, checkpoint lag. Throughput is vanity; these are health.

## Concepts covered

1. **Watermarks: deciding when "late" means "too late."** Event time is when something happened; processing time is when your job saw it — they constantly disagree. The watermark is the threshold before which data is declared late: Spark tracks the max event time seen, subtracts it, and events below it are *dropped* from the aggregation (not errored). The tradeoff is real: a 30-minute watermark means windows finalize half an hour late. Set it from your measured lateness distribution, and monitor the dropped-late rate as a first-class metric.
2. **Exactly-once: checkpoints, sinks, and the idempotency contract.** Two guarantees bolted together: offsets are checkpointed transactionally with the output (restart resumes after the last committed offset), and the sink must make replays harmless — Delta commits each micro-batch as one transaction version, so a replayed batch is a no-op. The checkpoint location is sacred: lose it and the stream loses its memory. Custom sinks are your half of the contract — every duplicate incident I've debugged ended at a non-idempotent sink.
3. **foreachBatch: the escape hatch you'll actually use.** For what built-in sinks can't express — a `MERGE` into a slowly-changing table, batch model scoring, atomic-ish writes to two tables — `foreachBatch` runs arbitrary batch code per micro-batch. Two sharp edges: `batch_id` is your idempotency key (design the function to tolerate replays), and `foreachBatch` gives at-least-once *invocation* of your function, so never put non-idempotent side effects (emails, charges) inside it.
4. **The SwiftPay real-time fraud example.** Two streams: one computes per-card velocity features with a measured 10-minute watermark, the other scores authorizations via `foreachBatch` and MERGEs risk scores into the serving table the auth API reads — median 40 seconds swipe-to-decision. What bit them in month two: a mobile SDK bug sent timestamps 12 hours in the future, advancing the watermark and dropping *legitimate* events as late — caught within an hour only because the dropped-late rate was monitored. The fix: a sanity filter on event timestamps, now the first thing added to any event-time pipeline.
5. **Late data as a designed policy.** Measure the lateness distribution first; quarantine late and out-of-order events with their arrival metadata instead of silently dropping them; decide explicitly what "correct" means for corrections (that's a batch reconciliation job, not the stream pretending); alert on the watermark itself.
6. **When streaming is the wrong call.** An "within an hour" SLA is a micro-batch problem — don't pay streaming complexity for batch requirements. Kafka orders within a partition, not across them. And if nobody will own the monitors, streams fail in slow silent ways — batch is the honest choice.

## Hands-on exercises

1. **Monitor a cold chain — and quarantine the late readings.** "ColdHaul" streams temperature readings from pharma reefer trucks; anything more than 10 minutes late must be excluded from compliance aggregates but kept for investigation. Build a synthetic sensor stream (~15% readings 11–20 minutes late), apply a 10-minute watermark computing 5-minute windowed averages per truck into Delta, route late readings to quarantine, and verify the counts reconcile.
2. **Attribute purchases to clicks with `foreachBatch`.** Marketing wants purchases matched to the click that drove them (same user, same product, purchase within 15 minutes of the click) — merge logic too complex for a plain streaming sink. Stream clicks, keep a static purchases table, and write a `foreachBatch` function that `MERGE`s attributions into Delta keyed on click_id. Then simulate a crash-replay by invoking the function twice with the same `batch_id` and prove the second call changes nothing.
3. **The restart drill: prove exactly-once survives a stop.** A payment ledger ingests CSV files via Auto Loader; the stream stops for maintenance mid-day. Stream wave 1 with a checkpoint, stop, add wave 2, restart with the same checkpoint, and verify the ledger — then run the same source into a second table with a *fresh* checkpoint to show exactly what losing the checkpoint costs.

## Solutions

- `solution-1-watermarked-cold-chain-aggregates-with-l-py.py` — Synthetic reefer-truck sensor stream with 15% late readings; 10-minute watermarked windowed aggregates plus the late-reading quarantine.
- `solution-1-watermarked-cold-chain-aggregates-with-l-sql.sql` — SQL reconciliation checks proving windowed + quarantined counts equal the total generated.
- `solution-2-foreachbatch-attribution-with-a-replay-t.py` — `foreachBatch` click→purchase attribution with a same-`batch_id` replay test proving idempotency.
- `solution-3-restart-drill-with-checkpoint-vs-no-chec.py` — Two-wave CSV restart drill comparing the checkpointed ledger against the fresh-checkpoint duplicate table.

## Prerequisites

All three exercises run on **Databricks Free Edition**. There's no Kafka on Free Edition, so the streams use the built-in `rate` source and file-based Auto Loader — the watermark, checkpoint, and `foreachBatch` mechanics are identical.
