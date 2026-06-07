# PRD 01 — Brain: Context Retrieval (the SPINE / moat)

**Owner:** A · **Roadmap:** Phase 2 · **Requirements:** BRN-01..04, FBK-01
**Depends on:** Foundation contract only (parallel with Voice & Live)

## Mission

Make the clone **answer a follow-up with the right, real specifics retrieved from the speaker's Moss namespace — and make that retrieval visible.** This is the moat and the demo's killer moment. If this lands in text, the whole pitch works; if it doesn't, we fall back to Slack-summary-only. **You own the most important workstream.**

## What you're building

Replace `brain/stub.py` with the real `handle_turn(incoming_text, persona_id) -> TurnResult`:
```
retrieve(Moss, namespace=persona_id, query=incoming_text)  →  k chunks
        ↓
LLM(system_prompt[persona], context=chunks, question=incoming_text)  →  grounded answer
        ↓
return TurnResult(response_text=answer, retrieved=chunks)   # chunks power the on-screen trace
```

## Scope

**In:**
- **BRN-01** Ingest each persona's week of context (Slack / calendar / Linear export) → chunk → index into Moss under `moss_namespace` (= `persona_id`). Hardcoded export files are fine for the demo.
- **BRN-02** Real `handle_turn`: retrieve from the speaker's namespace → LLM → grounded answer with the real specifics.
- **BRN-03** Populate `TurnResult.retrieved` so the caller can render `🔎 Moss → [chunk used]`. Retrieval must be **observable**, not just internal.
- **BRN-04** Make a **scripted demo question** about an absent teammate's work return the correct, specific answer in text (prove the moment without voice).
- **FBK-01** Wire the **Slack-summary-only fallback** path: if the spine doesn't land, the same idea ships as a posted summary instead of live Q&A.

**Out:** voice (PRD 02), the LiveKit room (PRD 03), the contract signature (locked in Foundation — don't change it).

## Success criteria (what must be TRUE)

1. Each persona's context is chunked and indexed in Moss under a per-user namespace.
2. `handle_turn` retrieves from the speaker's namespace and returns a factually grounded answer with the real specifics.
3. `TurnResult.retrieved` is populated and the harness shows the chunk(s) used next to the answer.
4. A scripted demo question (e.g. *"What's blocking the ingestion pipeline?"*) returns the correct specific answer in text.
5. **Go/no-go:** if 2–4 aren't landing after the first build block, the Slack-summary-only fallback is ready.

## Suggested slices (you plan the details)

- `02-01` Ingestion: export → chunking strategy → index into Moss namespace per persona.
- `02-02` Real `handle_turn`: retrieval + prompt assembly + LLM call; populate `retrieved`.
- `02-03` Scripted demo-question validation + Slack-summary-only fallback.

## Design decisions that are YOURS

- Chunking granularity & metadata (what makes `ref` human-readable in the trace).
- How many chunks to retrieve / how to rank / threshold.
- Prompt design: how the system_prompt + retrieved context produce a *specific, in-character* answer (not a vague summary). **This is where the moat is won or lost** — a generic answer kills the demo.

## SDKs you touch

**Moss** (`inferedge-moss` Python — ingestion + namespaced retrieval) · LLM (TrueFoundry gateway or direct). **Ground every Moss call in current docs** — use `source-driven-development` + the Moss SDK docs; do not guess API names.

## Integration points

You produce the real `handle_turn`. When ready, Voice (PRD 02) and Live (PRD 03) swap their import from `brain.stub` → `brain.contract`. No signature change = free swap.

## Next

`/gsd-plan-phase 2` for a detailed task plan, or build from the slices. **Restart Claude Code first.**
