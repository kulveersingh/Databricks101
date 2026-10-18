# Fine-Tune Mistral on Your Own Data: SFT, LoRA, and MLflow

A base model knows the world but nothing about your business. In this post you'll learn how to teach Mistral 7B your domain — support-ticket drafting, in this case — using supervised fine-tuning (SFT) with LoRA on Databricks, tracking every run in MLflow. You'll see why LoRA's small trainable adapters make fine-tuning a single-GPU job, how to build a fine-tune → evaluate → deploy loop, and what to log so any training run is reproducible months later.

![Architecture diagram](./diagram.png)

The diagram shows the full fine-tuning loop as five stages: (1) prepare data — a curated 7,000-ticket training set plus a 1,000-ticket held-out set; (2) train with QLoRA, learning a small rank-16 adapter while the 4-bit base model stays frozen, all tracked in MLflow; (3) evaluate with an LLM judge against the held-out set as a hard gate — pass and register, fail and stop; (4) register the adapter in Unity Catalog and A/B serve it at 10% traffic with inference tables logging production traffic; and (5) close the loop by turning heavily rewritten drafts into new training data, so the model compounds over time.

## Concepts covered

1. **Supervised fine-tuning (SFT).** The core technique: show the model thousands of input→output pairs from your domain so it learns to produce *your* outputs. Conceptually it's the same next-token training the base model got — just on your data, teaching tone, format, and task behavior.
2. **LoRA (Low-Rank Adaptation).** Instead of updating all 7 billion parameters, you learn tiny low-rank update matrices per layer — roughly 1% of the parameters. Training is faster and cheaper, and the adapter is a megabyte-scale file you can version, A/B test, and roll back like code.
3. **QLoRA.** Load the frozen base model in 4-bit quantization so a 7B model fits in ~5GB of GPU memory instead of ~14GB. A Mistral 7B fine-tune becomes a single-GPU lunch-break job, with only a small quality trade-off for most domain-adaptation tasks.
4. **The fine-tune → evaluate → deploy loop.** Prepare data, train with MLflow tracking, evaluate against a held-out set *and* the base model, register the adapter in Unity Catalog, A/B deploy on a serving endpoint, then observe production traffic via inference tables and feed failures back as new training data.
5. **Evaluation as a gate.** A model that "feels better" in a notebook but was never scored against the base model on held-out data is a vibes-based deploy. The eval gate decides ship vs. no-ship — it's a gate, not a suggestion.
6. **MLflow tracking for fine-tuning.** Beyond autologged loss curves, log what makes a run reproducible: the dataset hash (which data trained this model), the base model ID plus LoRA rank/alpha config, eval scores on the held-out set as metrics, and the chat template as an artifact (template mismatch between training and inference is a classic silent failure).
7. **When fine-tuning is the wrong call.** LoRA teaches behavior (tone, format, escalation rules) far more reliably than new facts — knowledge belongs to RAG. With only ~200 examples you're mostly memorizing (try few-shot first), and if the real problem is the prompt, fine-tuning wastes a week — evaluate the base model first.

## Hands-on exercises

All three run on Databricks Free Edition's CPU-only serverless compute — no model downloads, all data generated in the notebook. They cover the three parts of the loop you own regardless of hardware: data curation, LoRA mechanics, and the eval gate.

1. **Curate TicketWise's training data.** Take a raw export of 300 support tickets (duplicates and one-liner exchanges included), dedupe near-identical customer messages, drop thin responses, split into a stratified 80/20 train/heldout split, and hash the training set — proving zero leakage between the splits.
2. **Feel the LoRA rank tradeoff.** With no GPU and no model download, use pure linear algebra: build a structured 512×512 weight-update matrix, approximate it with truncated SVD at ranks 4 and 16, and compare relative error vs. trainable-parameter percentage — then repeat with pure noise to see why structured updates favor LoRA.
3. **Run the eval gate.** For 40 heldout tickets, score "base" drafts (fluent, generic, no policy citations) against "fine-tuned" drafts with a deterministic rubric (+1 policy keyword, +1 tone marker, 0 if under 20 words), log the means to one MLflow run, and make a ship/no-ship call with the margin stated.

## Solutions

- `solution-1-dataset-curation.py` — Generates 300 synthetic tickets, dedupes on normalized customer text, drops one-liners, makes the stratified train/heldout split, verifies no heldout leakage, and logs stage counts plus the dataset hash to MLflow.
- `solution-2-lora-rank-tradeoff.py` — Builds structured and pure-noise ΔW matrices, computes rank-4 and rank-16 truncated-SVD approximations, and reports relative reconstruction error alongside trainable-parameter percentages.
- `solution-3-the-eval-gate.py` — Generates 40 heldout tickets with policy keywords, implements the deterministic rubric judge, scores both candidate drafts, logs both means to MLflow, and prints the ship/no-ship decision.

## Prerequisites

- Databricks Free Edition — all exercises run on CPU-only serverless compute with data generated in the notebook (no model downloads).
- Basic Python and familiarity with MLflow tracking (blog 11 covered MLflow fundamentals).
- **GPU note:** the real SFT run from the post needs a GPU cluster — Free Edition is CPU-only serverless, so training Mistral itself isn't possible here. Everything above runs free; the training step is the one you rent the GPU for.
