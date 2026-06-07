# Standup Proxy — Workstream PRDs (split for the team)

This folder is **the structure for splitting the build.** Each PRD is self-contained: open your file, read top to bottom, start working. You don't need to read anyone else's.

> Full project context: `../.planning/PROJECT.md`, `../.planning/REQUIREMENTS.md`, `../.planning/ROADMAP.md`.

## Demo north star (what everyone serves)

In a standup, the PM asks an **absent teammate (Person A)** for a status update and a follow-up. **A's clone** answers — in A's **cloned voice**, with the **real specifics pulled live from A's context (Moss)**, shown on screen. That retrieval-with-real-specifics moment is the moat. If everything else fails, that must work.

## The split (5 files, real owners)

| File | Lane | Owner | Hands off |
|------|------|-------|-----------|
| `00-FOUNDATION.md` | repo + the two shared contracts | **Tony** (first) | the scaffold + stubs everyone builds on |
| `01-LINEAR-CONTENT.md` | author Person A's context → a corpus file | **Melody** | the **corpus file** → Nuha |
| `02-MOSS-RETRIEVAL.md` | corpus → Moss → `retrieve()` | **Nuha** | `retrieve()` → Tony |
| `03-VOICE.md` | clone A's voice (Qwen) + STT + cached lines | **Nuha** | the **voice config** → Tony |
| `04-LIVE-AGENT.md` | the LiveKit agent + room + Slack summary | **Tony** | nothing — the demo runs here |

> **Note:** Nuha holds two files (`02` Moss-Retrieval + `03` Voice). They're independent and Voice is light — see "Build order" for how to sequence them. If that's too much, Voice can move to Tony; say so.

## The two handoffs that keep everyone independent

Everything connects through **two fixed contracts** (both defined in `00-FOUNDATION.md`). Agree on these once, then nobody blocks anyone:

1. **The corpus file** — `data/<persona>_corpus.jsonl`, one JSON record per line:
   ```json
   {"id": "lin-eng-412", "source": "linear", "ref": "ENG-412 Auth migration", "text": "..."}
   ```
   **Melody writes it. Nuha reads it.** Nuha works against a sample corpus until Melody's real one lands — no waiting.

2. **`retrieve()`** — `async retrieve(query_text, persona_id) -> list[RetrievedChunk]`.
   **Nuha builds it. Tony calls it** inside the LiveKit hook. Tony works against a stub until Nuha's real one lands — no waiting.

3. **The voice config** — **Nuha produces it. Tony plugs it** into LiveKit's voice slot. Tony uses a placeholder voice until then.

## How the pieces fit (grounded in Moss × LiveKit docs)

LiveKit runs the agent (room, listen, turn-taking, speak). Moss has an **official LiveKit integration**: on each user turn (`on_user_turn_completed`), Moss is queried and the results are injected into the LLM's context. So:
- **LiveKit** = the agent + room (Tony)
- **Moss** = the memory, injected via its hook (Nuha's `retrieve()` is the query)
- **LLM plugin** = writes the answer from the injected context
- **Qwen / Minimax** = the cloned voice (Nuha)

## Build order (dependency-smart)

1. **Tony first (~30 min):** scaffold the repo, persona config, the **corpus format spec**, a **sample corpus**, the **`retrieve()` stub**, and a text harness. Publish → team splits.
2. **Parallel:**
   - **Melody:** author Person A's Linear content → export to the corpus format. *(This is the unblocker — Moss can't load until it exists, so start here.)*
   - **Nuha:** clone A's voice in Qwen + pre-cache lines (independent, fast). Then start Moss-Retrieval against the **sample corpus**.
   - **Tony:** build the LiveKit agent against the **`retrieve()` stub** + a placeholder voice.
3. **Merge:** Nuha loads Melody's real corpus + finishes `retrieve()`; Tony swaps stub→real `retrieve()` and placeholder→Nuha's voice, wires the 🔎 trace + Slack summary, rehearses the 2-min script.

## Rules

- **Don't change a contract alone.** The corpus format, `retrieve()` signature, and voice handoff are shared surfaces — change them only by team agreement.
- **Source-driven, no hallucinated SDKs.** Moss / LiveKit / Qwen / Minimax — ground every call in current docs (the `source-driven-development` skill, the `livekit-docs` MCP, the Moss×LiveKit page).
- **Go/no-go:** if `retrieve()` doesn't return the right chunk after the first block → fall back to **Slack-summary-only**. Protect the demo.
