# PRD 00 — Foundation (SHARED · Tony does this FIRST)

**Owner:** Tony (before the team splits) · **Roadmap:** Phase 1 · **Requirements:** FND-01..04

## Mission

Stand up the repo and **lock the two shared contracts** so Melody, Nuha, and Tony can each work alone without colliding. Small and fast — the deliverable that unblocks everyone is **the contracts + stubs**, not finished features.

## The two contracts (ratify with the team, then lock)

### Contract 1 — the context corpus (Melody → Nuha)

A file Melody produces and Nuha consumes: `data/<persona>_corpus.jsonl`, one JSON object per line.

```json
{"id": "lin-eng-412", "source": "linear",   "ref": "ENG-412 Auth migration", "text": "Auth migration: blocked on the token-refresh race; waiting on infra to bump the Redis TTL."}
{"id": "sl-0603",     "source": "slack",    "ref": "#auth 2026-06-03",       "text": "Confirmed the OAuth callback works in staging; prod rollout gated on the TTL fix."}
```

Fields: `id` (unique), `source` (`linear`|`slack`|`calendar`), `ref` (human-readable locator — this is what shows in the 🔎 on-screen trace), `text` (the content chunk).

### Contract 2 — `retrieve()` (Nuha → Tony)

```python
# brain/retrieval.py — the shape. Nuha implements; Tony calls it.
from dataclasses import dataclass

@dataclass
class RetrievedChunk:
    text: str       # the content used to ground the answer
    source: str     # "linear" | "slack" | "calendar"
    ref: str        # human-readable locator → shown in the 🔎 trace
    score: float    # retrieval similarity

async def retrieve(query_text: str, persona_id: str) -> list[RetrievedChunk]:
    """Query the persona's Moss index for context relevant to the question.
       Called in text (Nuha's tests) AND inside LiveKit's on_user_turn_completed (Tony)."""
```

### Persona config (FND-03)

```python
@dataclass
class Persona:
    id: str             # namespace key, e.g. "person_a"
    name: str           # display name
    system_prompt: str  # character/voice + role grounding for the LLM
    voice_id: str       # cloned-voice handle (Nuha fills this from Qwen)
    moss_index: str     # usually == id
```

## What Tony ships in Foundation

1. Python repo + `.env` loader (Moss, LLM, LiveKit, Qwen/Minimax keys — **no keys committed**).
2. `pip install moss livekit-agents livekit-plugins-openai livekit-plugins-deepgram` (per the Moss×LiveKit page).
3. `brain/retrieval.py` — the `RetrievedChunk` dataclass + `retrieve()` **stub** that returns canned chunks (so Tony & Nuha both start).
4. `personas.py` — the `Persona` dataclass + 2 hardcoded personas.
5. `data/sample_corpus.jsonl` — 3–5 fake records in the corpus format (so Nuha can load something on day one, before Melody's real content).
6. `scripts/harness.py` — reads a question, calls `retrieve()`, prints the chunks + a draft answer. The text test bench.

## Success criteria

1. Repo runs; deps installed; `.env` loads; no keys committed.
2. `from brain.retrieval import retrieve` works (stub) and `personas.py` loads 2 personas.
3. `data/sample_corpus.jsonl` exists in the agreed format.
4. Running the harness prints chunks + a draft answer (using the stub + sample corpus).

## Hand-off to the team

The moment the stub `retrieve()`, persona config, sample corpus, and harness exist → **publish and split.** Tell the team:
- **Melody:** produce `data/person_a_corpus.jsonl` in the format above.
- **Nuha:** import `retrieve` from `brain.retrieval` (real, once you build it) — replace the stub. Use `sample_corpus.jsonl` until Melody's lands.
- **Tony (you):** build the agent calling the stub `retrieve()`, swap to real later.

## Next

`/gsd-plan-phase 1` for a detailed task plan, or build from the list. **Restart Claude Code first** (GSD was just installed).
