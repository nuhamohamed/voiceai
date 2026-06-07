# PRD 02 — Moss Retrieval (the `retrieve()` brain)

**Owner:** Nuha · **Roadmap:** Phase 2 (Brain, retrieval half) · **Requirements:** BRN-01 (load), BRN-02, BRN-03, BRN-04, FBK-01
**Works alone against:** the corpus format + `retrieve()` shape in `00-FOUNDATION.md`. **Hands off:** `retrieve()` → Tony.

## Mission

Turn Person A's corpus into a searchable **Moss** memory and build the one function that finds the right piece: **`retrieve(query_text, persona_id)`**. This is the live retrieval that makes the answer real — the moat's engine. You prove it works in **plain text**, no LiveKit needed.

## What you build

1. **Load** the corpus into a **Moss index** (one index per persona, `index_name = persona_id`):
   - read `data/<persona>_corpus.jsonl` → chunk if needed → `MossClient` `load_index()` / index it.
2. **Build `retrieve()`** over `MossClient.query(index_name=persona_id, query_text, QueryOptions(top_k=...))`, mapping each Moss hit → `RetrievedChunk(text, source, ref, score)` (so the `ref` flows to Tony's 🔎 trace).
3. **Tune** `top_k` / `QueryOptions` so the scripted demo question returns the **right** chunk near the top.
4. **Prove BRN-04 in text:** the scripted follow-up question → `retrieve()` returns the auth-migration blocker chunk. Print it.
5. **FBK-01 fallback:** if retrieval can't be made reliable in time, help wire the Slack-summary-only path (the simpler demo).

## Scope

**In:** loading corpus → Moss, `retrieve()`, query tuning, the text-proof. **Out:** authoring content (Melody), voice (your other PRD `03`), the LiveKit room/agent (Tony — he *calls* your `retrieve()`).

## Success criteria

1. Each persona's corpus is loaded into its own Moss index.
2. `retrieve(question, persona_id)` returns relevant `RetrievedChunk`s with readable `ref`s.
3. The scripted demo question returns the correct specific chunk (proven in the text harness, no voice/room).
4. Fallback path identified if the spine doesn't land.

## How to not wait on anyone

Start against **`data/sample_corpus.jsonl`** (shipped in Foundation) — build load + `retrieve()` + tuning before Melody's real content exists. When `person_a_corpus.jsonl` lands, just re-run the loader. **No code change.** Do this in parallel with your Voice PRD (`03`) — Voice first (it's fast and independent), then this.

## Design decisions that are yours

- Chunking (per record? split long text?) and what makes `ref` readable in the trace.
- `top_k`, the `alpha` / hybrid-search knobs in `QueryOptions`, score thresholds.
- Whether 2 personas = 2 indexes or 1 index + metadata filter (**verify against Moss docs** — the integration page didn't spell out namespaces; one index per persona is the simple read).
- Prompt shape for the draft answer in the text harness (so you can eyeball quality).

## SDKs you touch

**Moss** (`MossClient`, `query`, `QueryOptions`, `load_index`) + an LLM for the harness draft answer. **Ground every Moss call in the Moss×LiveKit page + Moss docs** — confirm exact signatures, don't guess.

## Next

`/gsd-plan-phase 2` (you + Melody share Phase 2 — your plan is the retrieval half), or build from the list. **Restart Claude Code first.**
