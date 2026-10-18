# Blog 16 — RAG on Databricks: From PDFs to Answers
# Exercise 2: the chunking shootout.
# Requires: Databricks Free Edition. Deterministic token-overlap embeddings are labeled stand-ins; at scale swap for GPU batch embeddings and a Vector Search index.

def chunk_fixed(doc, size=30, overlap=5):
    # naive: fixed word count, splits sections mid-sentence
    words, chunks, i = doc["text"].split(), [], 0
    while i < len(words):
        piece = words[i:i + size]
        chunks.append({"text": " ".join(piece), "source_doc": doc["doc_id"],
                       "section": "fixed", "version": doc["version"]})
        i += size - overlap
    return chunks

def chunk_section_aware(doc):
    # never cross a section boundary: one chunk per section
    chunks, cur, section = [], [], "intro"
    for line in doc["text"].split("\n"):
        if line.startswith("## "):
            if cur: chunks.append({"text": " ".join(cur), "source_doc": doc["doc_id"],
                                           "section": section, "version": doc["version"]})
            section, cur = line[3:], []
        elif line.strip(): cur.append(line)
    if cur: chunks.append({"text": " ".join(cur), "source_doc": doc["doc_id"],
                                   "section": section, "version": doc["version"]})
    return chunks

def build(docs, chunker):
    idx = [c for d in docs for c in chunker(d)]
    for c in idx: c["vec"] = embed(c["text"], VOCAB)
    return idx

# golden set: question -> (topic, full expected answer text)
GOLDEN = [
    ("how do I rotate an API key after rotation completes", "api-keys", QA["api-keys"][0][1]),
    ("which admin scopes can manage other keys", "api-keys", QA["api-keys"][1][1]),
    ("when are invoices issued with line item breakdown", "billing", QA["billing"][0][1]),
    ("refund processed within 10 business days", "billing", QA["billing"][1][1]),
    ("configure SAML with IdP metadata URL", "sso", QA["sso"][0][1]),
    ("SCIM provisioning syncs users every 15 minutes", "sso", QA["sso"][1][1]),
    ("webhook retry exponential backoff 8 attempts", "webhooks", QA["webhooks"][0][1]),
    ("verify signatures with HMAC SHA256", "webhooks", QA["webhooks"][1][1]),
    ("CSV Parquet export 10M rows multipart", "data-export", QA["data-export"][0][1]),
    ("scheduled exports 02:00 UTC S3 bucket", "data-export", QA["data-export"][1][1]),
]

def answer_completeness(idx):
    hits = 0
    for q, topic, answer in GOLDEN:
        qv = embed(q, VOCAB)
        best = max(idx, key=lambda c: cosine(qv, c["vec"]))
        if topic in best["source_doc"] and answer in best["text"]:
            hits += 1
    return hits

naive = answer_completeness(build(docs, chunk_fixed))
aware = answer_completeness(build(docs, chunk_section_aware))
print(f"answer completeness@1 — fixed-size: {naive}/10 | section-aware: {aware}/10")
assert aware >= 8 and aware >= naive
