# Standup Proxy — Workstream PRDs (split for the team)

This folder splits the build across the team. **Each PRD is outcome-focused: your role, the final outcome you own, and the one interface you must honor — not step-by-step instructions.** How you build your part is yours.

## Demo north star (what everyone serves)

In a standup, the PM asks an **absent teammate (Person A)** for a status update and a follow-up. **A's clone** answers — in A's **cloned voice**, with the **real specifics pulled live from A's context (Moss)**, shown on screen. That retrieval-with-real-specifics moment is the moat. If everything else fails, that must work.

## The split

| File | Lane | Owner | Hands off |
|------|------|-------|-----------|
| `00-FOUNDATION.md` | repo + the shared contracts | **Tony** (first) | the scaffold + stubs everyone builds on |
| `01-LINEAR-CONTENT.md` | Person A's real context → a corpus file | **Melody** | the **corpus file** → Nuha |
| `02-MOSS-RETRIEVAL.md` | corpus → Moss → `retrieve()` | **Nuha** | `retrieve()` → Tony |
| `03-VOICE.md` | make the clone sound like Person A | **Nuha** | the **voice + STT config** → Tony |
| `04-LIVE-AGENT.md` | the LiveKit agent + room + Slack summary | **Tony** | nothing — the demo runs here |

> Nuha holds two files (`02` + `03`). They're independent, and `03` is light if you take the pre-rendered-clone path. If it's too much, Voice can move to Tony.

## The handoffs that keep everyone independent

Everything connects through fixed interfaces (defined in `00-FOUNDATION.md`). Honor these and nobody blocks anyone:

1. **Corpus file** — `data/<persona>_corpus.jsonl`, one record per line: `{"id","source","ref","text"}`. **Melody writes, Nuha reads** (Nuha uses a sample until Melody's lands).
2. **`retrieve()`** — `async retrieve(query_text, persona_id) -> list[RetrievedChunk]`. **Nuha builds, Tony calls** (Tony uses a stub until Nuha's lands).
3. **Voice + STT config** — **Nuha produces, Tony plugs in** (Tony uses a placeholder voice until then).

## How the pieces fit (grounded in Moss × LiveKit docs)

- **LiveKit** runs the agent + room (Tony). Moss plugs into its `on_user_turn_completed` hook: query Moss, inject results into the LLM context before it answers.
- **Moss** = the memory; Nuha's `retrieve()` is the query (the moat).
- **LLM plugin** writes the answer from the injected context.
- **Cloned voice** (Nuha) — pre-rendered for the scripted lines; optional live clone via LiveKit Custom Voices if the plan allows. See `03`.

## How each person plans the details

- **Tony** re-plans his lanes (Foundation + Live) with GSD (`/gsd-plan-phase`).
- **Melody & Nuha** build straight from their PRD — the outcome and the interface are fixed; the method is theirs.

## Rules

- **Don't change an interface alone.** The corpus format, `retrieve()` signature, and voice handoff are shared surfaces — change only by team agreement.
- **Source-driven, no hallucinated SDKs.** Ground every Moss / LiveKit / Qwen / Minimax call in current docs (the `source-driven-development` skill, the `livekit-docs` MCP, the Moss × LiveKit page).
- **Go/no-go (protect the moat):** if `retrieve()` can't surface the right chunk, fall back **first** to the **text-on-screen** version (the moat still shows) — **Slack-summary-only** is the last resort.
