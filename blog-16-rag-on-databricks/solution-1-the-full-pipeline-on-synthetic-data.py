# Blog 16 — RAG on Databricks: From PDFs to Answers
# Exercise 1: the full pipeline on synthetic data.
# Requires: Databricks Free Edition. Deterministic token-overlap embeddings are labeled stand-ins; at scale swap for GPU batch embeddings and a Vector Search index.

import math, random, re
from collections import Counter

rnd = random.Random(2026)
TOKEN = re.compile(r"[a-z0-9]+")
TOPICS = ["billing", "api-keys", "sso", "webhooks", "data-export"]
QA = {
    "billing": [("invoice", "invoices are issued on the first of each month and include a detailed line item breakdown for every charge"),
                ("refund", "refunds are processed within 10 business days and appear on the original payment method automatically")],
    "api-keys": [("rotation", "rotate keys from Settings > API Keys > Rotate; old keys stay valid for 24 hours after rotation completes"),
                 ("scopes", "keys support read, write, and admin scopes; admin scope can manage other keys and billing settings")],
    "sso": [("saml", "configure SAML via Settings > Security with your IdP metadata URL and upload the signing certificate"),
            ("scim", "SCIM provisioning syncs users every 15 minutes and deactivates accounts removed from the identity provider")],
    "webhooks": [("retry", "failed webhooks retry with exponential backoff across 8 attempts over a 24 hour window"),
                 ("signing", "verify signatures with the X-Webhook-Secret header using HMAC SHA256 on the raw request body")],
    "data-export": [("csv", "exports support CSV and Parquet formats up to 10M rows per file with automatic multipart splitting"),
                    ("schedule", "scheduled exports run daily at 02:00 UTC and deliver to the configured S3 bucket prefix")],
}

def gen_articles(n=200):
    docs = []
    for i in range(n):
        topic = TOPICS[i % len(TOPICS)]
        secs = "\n".join(f"## {s}\n{body}\n" for s, body in QA[topic])
        docs.append({"doc_id": f"{topic}-{i//len(TOPICS)}",
                     "text": f"# {topic} guide\n{secs}", "version": "v3"})
    return docs

def chunk(doc, size=120, overlap=20):
    words, chunks, i = doc["text"].split(), [], 0
    section = "intro"
    while i < len(words):
        piece = words[i:i+size]
        for w in piece:                      # track current section heading
            if w == "##": section = piece[piece.index(w)+1] if piece.index(w)+1 < len(piece) else section
        chunks.append({"text": " ".join(piece), "source_doc": doc["doc_id"],
                       "section": section, "version": doc["version"]})
        i += size - overlap
    return chunks

def build_vocab(docs):
    vocab = {}
    for d in docs:
        for t in TOKEN.findall(d["text"].lower()):
            if t not in vocab:
                vocab[t] = len(vocab)
    return vocab

def embed(text, vocab):
    # deterministic token-overlap vector: stands in for BGE on Free Edition.
    # Real embeddings capture semantics; this captures keyword overlap —
    # enough to exercise the chunking/retrieval/gating logic on synthetic docs.
    counts = Counter(TOKEN.findall(text.lower()))
    v = [0.0] * len(vocab)
    for t, c in counts.items():
        if t in vocab:
            v[vocab[t]] = c
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]

def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))

docs = gen_articles()
VOCAB = build_vocab(docs)
index = [c for d in docs for c in chunk(d)]
for c in index:
    c["vec"] = embed(c["text"], VOCAB)

def ask(question, k=3):
    qv = embed(question, VOCAB)
    ranked = sorted(index, key=lambda c: cosine(qv, c["vec"]), reverse=True)[:k]
    cites = "; ".join(f"[source: {c['source_doc']}, section: {c['section']}, {c['version']}]" for c in ranked)
    return ranked, cites

top, cites = ask("how do I rotate an API key")
assert any("api-keys" in c["source_doc"] for c in top), "retrieval missed the right doc"
print("answer: rotate via Settings > API Keys > Rotate; old keys stay valid for 24 hours.")
print("citations:", cites)
