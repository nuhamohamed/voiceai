# PRD 00 — Foundation & Contract (SHARED · do this FIRST)

**Owner:** one person (do this before the team splits) · **Roadmap:** Phase 1 · **Requirements:** FND-01..04

## Mission

Stand up the Python project and **lock the single integration seam** — `handle_turn` — plus persona config and a text harness, so the other three workstreams can build in parallel against a stable contract. This phase is small and fast on purpose. **The deliverable that unblocks everyone is the contract module + a working stub**, not a finished brain.

## ⚑ The contract (ratify as a team before anyone codes against it)

This is the one shared surface. It refines the handoff's `handleTurn(text) -> {responseText}` in two ways the requirements force:
- adds **`persona_id`** input — the brain must know *whose* clone is answering to pick the right Moss namespace + system prompt ("namespace = user").
- returns **`retrieved`** chunks, not just text — because retrieval must be shown on screen (BRN-03) and overlaid in the demo.

```python
# brain/contract.py  — LOCK THIS. Everyone imports from here.
from dataclasses import dataclass, field

@dataclass
class RetrievedChunk:
    text: str       # the chunk content used to ground the answer
    source: str     # "slack" | "linear" | "calendar"
    ref: str        # human-readable locator, e.g. "Linear ENG-412", "#ingestion 2026-06-03"
    score: float    # retrieval similarity score

@dataclass
class TurnResult:
    response_text: str                          # what the clone says (always present)
    retrieved: list[RetrievedChunk] = field(default_factory=list)  # chunks used → visible retrieval

def handle_turn(incoming_text: str, persona_id: str) -> TurnResult:
    """
    The brain. I/O-agnostic: identical call from the text harness AND the live voice loop.
      incoming_text — the question/utterance directed at the clone
      persona_id    — which teammate's clone answers (selects Moss namespace + system prompt)
    Pipeline: retrieve(Moss, namespace=persona_id) -> LLM(system_prompt, context, question) -> answer
    """
```

### Persona config shape (FND-03)

```python
@dataclass
class Persona:
    id: str             # namespace key, e.g. "melody"
    name: str           # display name
    system_prompt: str  # character/voice + role grounding for the LLM
    voice_id: str       # cloned-voice handle for TTS (Qwen / Minimax)
    moss_namespace: str # usually == id
```

### The stub (ship this so Voice & Live can start)

```python
# brain/stub.py — drop-in until Brain (PRD 01) ships the real handle_turn
from brain.contract import TurnResult, RetrievedChunk

def handle_turn(incoming_text: str, persona_id: str) -> TurnResult:
    return TurnResult(
        response_text=f"[{persona_id} clone] (stub) heard: {incoming_text!r}",
        retrieved=[RetrievedChunk("stub context chunk", "linear", "ENG-000", 0.99)],
    )
```

## Scope

**In:** repo + dependency management; `.env` secret loader (Moss / LLM / voice / LiveKit keys); `brain/contract.py`; `brain/stub.py`; 2 hardcoded `Persona`s as config loadable by `persona_id`; a text harness (`scripts/harness.py`) that reads a transcript line, calls `handle_turn`, prints `response_text` + the retrieval trace.

**Out:** real Moss retrieval (→ PRD 01), any voice/audio (→ PRD 02), any LiveKit/room code (→ PRD 03). Do **not** start meeting plumbing here.

## Success criteria (what must be TRUE)

1. Repo runs in Python; deps installed; secrets load from `.env`; **no keys committed** (`.gitignore` already excludes `.env`).
2. `from brain.contract import handle_turn` works and is importable by both the harness and (later) the voice loop.
3. 2 personas load by `persona_id` (name + system_prompt + voice_id + moss_namespace).
4. Running the harness on a transcript line prints a response + a `🔎 Moss → [chunk]`-style trace (using the stub at this point).

## Suggested slices (you plan the details)

- `01-01` Project scaffold + dependency/secret management (`.env` loader, `.env.example`).
- `01-02` `brain/contract.py` (the dataclasses + signature) + `brain/stub.py` + persona config loader.
- `01-03` `scripts/harness.py`: transcript line → `handle_turn` → print `response_text` and `retrieved` trace.

## Hand-off to the team

The moment `brain/contract.py` + `brain/stub.py` exist and the harness prints something, **post it to the team and split.** Brain owner replaces the stub; Voice + Live import the stub and start. Tell the others: import `handle_turn` from `brain.contract` (real) or `brain.stub` (until Brain lands).

## SDKs you touch

LLM gateway (TrueFoundry or direct) for the stub→real path; Moss client init (used by PRD 01). Ground in current docs — `source-driven-development` skill.

## Next

`/gsd-plan-phase 1` for a detailed task plan, or build straight from the slices above. **Restart Claude Code first** (GSD was just installed).
