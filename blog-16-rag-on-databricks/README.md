# RAG on Databricks: From PDFs to Answers

Blog 16 of the Databricks series. A support team drowns in repeat questions with three agents giving three different answers — the obvious fix is a chatbot, and the trap is that tutorials end at "embed your docs and query them" while production systems die in the gap. This post shows how to build a support-docs RAG chatbot on Databricks: chunking, open-source BGE embeddings, Vector Search, and open-source LLM generation — with the whole loop inside your VPC so no data ever reaches a third party.

![Architecture diagram](./diagram.png)

The diagram splits the system into two halves. OFFLINE — the knowledge pipeline: docs land in the lake (Autoloader → bronze Delta), get parsed and chunked (~512 tokens, 50 overlap, split on semantic boundaries), embedded on a GPU batch job (BGE/E5, merge on chunk hash so only changed chunks get re-embedded), stored as an embedding Delta table with metadata, indexed by managed Vector Search — all wrapped in Unity Catalog governance with row-level security. ONLINE — the query loop: user question → embed with the same BGE model → retrieve top-k chunks (low score escalates to a human) → generate with Llama/Mistral via Model Serving → answer with citations → feedback flows back into the golden dataset. A footer panel summarizes what made Northwind's support bot work: 180k chunks, confidence-gated escalation, a 150-question golden dataset, and consistency as the metric that mattered.

## Concepts covered

1. **The lakehouse is a natural RAG platform.** Documents are already data (with Unity Catalog lineage, access control, versioning); embeddings are just a vector column next to chunk text (time travel on your knowledge base: "what did the bot know last Tuesday"); and governance comes free — row-level security so the bot never answers from documents the user can't see.
2. **Chunking strategy matters more than the embedding model.** A bad split poisons everything downstream. Start at ~512 tokens with ~50 tokens of overlap, split on semantic boundaries (sections, paragraphs) rather than fixed character counts, and store metadata — source, page, section, version — because that metadata is what makes citations work.
3. **Embed with open-source models.** BGE and E5 are competitive with commercial embedding APIs, run on a single GPU, and keep your data in your VPC. Run batch embedding as a Databricks job; merge on chunk hash so doc updates only re-embed changed chunks instead of rebuilding the whole table.
4. **Vector Search is a managed index on your Delta table.** No separate vector database to operate, no sync pipeline to maintain — when the Delta table updates, the index syncs automatically. Use hybrid search (vector similarity + keyword) for technical docs, where exact term matches like "error code 0x4F" matter as much as semantics.
5. **Retrieve, then generate — all inside your account.** Embed the question with the same model, retrieve top-k chunks, stuff them into the prompt, and generate with an open-source LLM served from a Databricks Model Serving endpoint. For regulated industries, "no data crosses to a third-party API" is the entire point.
6. **The production details that make it work.** Citations on every answer (agents verify, customers trust), confidence-gated escalation ("I don't have a confident answer" instead of hallucinating), and a feedback loop where low-rated answers are reviewed weekly and feed back into chunking and prompt changes.
7. **The open-source trade-off is honest.** Data residency, cost at scale, and control (fine-tune the embedder on your jargon, swap the generation model, version everything in MLflow) — versus now operating GPU infrastructure and evaluating model quality yourself. High-volume and sensitive: open-source on Databricks. Low-volume and non-sensitive: commercial APIs are the pragmatic choice.

## Hands-on exercises

1. **Build a support-docs chatbot over 200 synthetic help articles.** Generate synthetic help articles with a fixed seed, chunk them with metadata (source, section, version), embed the chunks, and answer questions with citations.
2. **Run a chunking shootout and measure it.** Index the same articles twice — naive fixed-size chunks vs. section-aware chunks — and score both on answer completeness: for each golden question, does the top-1 retrieved chunk contain the entire correct answer text?
3. **Make the bot admit ignorance.** Build a confidence gate so the bot says "I don't have a confident answer" and escalates to a human when retrieval confidence is low, instead of hallucinating — then prove it refuses out-of-domain questions.

## Solutions

- `solution-1-the-full-pipeline-on-synthetic-data.py` — Full RAG pipeline on synthetic data: 200 fixed-seed help articles, metadata-tagged chunking, pseudo-embeddings, top-3 retrieval by cosine similarity, and citation-formatted answers.
- `solution-2-the-chunking-shootout.py` — Indexes the same articles with naive fixed-size vs. section-aware chunks and scores both on answer completeness over a golden question set; demonstrates measured proof that semantic boundaries win.
- `solution-3-the-confidence-gate.py` — Retrieval-confidence gate that refuses out-of-domain questions and escalates to a human instead of hallucinating; proves the refusal behavior on adversarial questions.

## Prerequisites

- All three exercises run on Databricks Free Edition with synthetic data — they use deterministic pseudo-embeddings (fixed seed) as a stand-in for BGE.
- GPU compute needed at real scale: rerun the chunking shootout with BGE-large embeddings on a GPU job; the scoring harness is identical. (Vector Search and GPU embedding are premium-tier features on real workspaces.)
