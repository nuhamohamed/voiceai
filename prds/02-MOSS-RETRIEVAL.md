# PRD 02 — Moss Retrieval (Nuha)

**Owner:** Nuha · **Lane:** Person A's memory — the retrieval (the moat's engine)
**You hand off:** `retrieve(query_text, persona_id)` → Tony's agent calls it.

## Your outcome

Given a question, the clone gets back the **right real context** from the person's Moss index — reliably enough that the scripted demo follow-up returns the correct, specific answer. This is the moat: if the answer is real, it's because your retrieval found the right chunk. You can prove it in plain text — no room or voice needed.

## The interfaces you must honor

- **In:** Melody's corpus file format (you load it).
- **Out:** `async retrieve(query_text, persona_id) -> list[RetrievedChunk]`, each chunk `{text, source, ref, score}`. Tony calls this; `ref` flows to the on-screen trace. The signature is fixed — the internals are yours.

## Done looks like

- Each persona's corpus is loaded into Moss.
- `retrieve()` returns relevant chunks with readable `ref`s.
- The scripted follow-up returns the correct specific chunk — shown in plain text.

## Worth knowing

- The path is documented: Moss × LiveKit uses `MossClient.query(index_name, query_text, QueryOptions(top_k=, alpha=))` and `load_index()` to preload. Confirm exact signatures on the Moss × LiveKit page.
- One-index-per-persona vs one-index-with-filter isn't spelled out in the docs — confirm before relying on it.
- You're unblocked from day one: build against `data/sample_corpus.jsonl` (in Foundation), then swap in Melody's real file later — no code change.
- Voice (PRD 03) is independent and lighter — many do it first, then this.

## Hand-off

Replace Foundation's stub `retrieve()` with the real one; Tony imports it unchanged.
