# Standup Proxy — Team Guide

When a teammate can't attend standup, **their clone joins in their cloned voice**, gives their update, and **answers follow-up questions about their work** — grounded in that person's real context (Slack / calendar / Linear) retrieved live from **Moss** — then posts action items to a Slack summary channel. (Moss Conversational AI Hackathon; 2 hardcoded personas for the demo.)

**The moat — what must work above all else:** the clone answers a live follow-up with the **right, real specifics retrieved from Moss**, shown on screen *and* spoken in the person's voice. If everything else fails, that one moment must land.

## Rules for everyone

- **Stack: Python + LiveKit.** **Source-driven — never hallucinate SDK APIs.** Ground every Moss / LiveKit / Qwen / Minimax call in current docs (the Moss × LiveKit page, the `livekit-docs` MCP).
- **No secrets in the repo** — keys live in `.env` (gitignored).
- **Don't change a shared interface alone** (see below) — that's what keeps the lanes decoupled.
- **Say *why*, not just *what* — for decisions that touch others.** If a choice affects a shared interface or another lane (you change the `retrieve()` shape, rename a corpus field, pick a library someone has to wire in), put the reason in your **commit message** *and* your `agent-status` **notes** (it shows on the dashboard). Lane-internal choices don't need broadcasting.
- **Branch per feature — don't build on `main`.** Each feature gets its own branch (`feat/<lane>-<short-name>`, e.g. `feat/nuha-moss`); open a PR to `main` when it's ready. Continue on the existing branch if one already exists for that feature; create a new one for new work. This keeps in-progress code from colliding on `main`. *(Exception: your tiny `agent-status/*.json` updates push straight to `main` so the dashboard stays live.)*

## Work breakdown

Each person owns one lane and connects through a fixed interface. Full briefs are in `prds/` (paste-ready kickoffs in `prds/handoffs/`).

| Owner | Lane | Delivers (the interface) | PRD |
|-------|------|--------------------------|-----|
| **Melody** | Person A's content | `data/person_a_corpus.jsonl` → Nuha | `prds/01-LINEAR-CONTENT.md` |
| **Nuha** | Moss retrieval + Voice | `retrieve(query_text, persona_id)` → Tony; cloned voice + STT config → Tony | `prds/02-MOSS-RETRIEVAL.md`, `prds/03-VOICE.md` |
| **Tony** | LiveKit agent + room + Slack summary | assembles everything — the demo runs here | `prds/00-FOUNDATION.md`, `prds/04-LIVE-AGENT.md` |

**The three fixed interfaces (change only by team agreement):**

1. **Corpus file** — `data/<persona>_corpus.jsonl`, one record/line: `{"id","source","ref","text"}`.
2. **`retrieve()`** — `async retrieve(query_text, persona_id) -> list[RetrievedChunk]` (each `{text, source, ref, score}`).
3. **Voice + STT config** — Nuha produces, Tony plugs into the LiveKit session.

Tony ships Foundation first (repo + stubs + a sample corpus), so everyone builds against stubs and never waits on each other.

## Coordination — check the dashboard, update your status (every session)

**Dashboard:** open `docs/index.html` — serve from the repo root (`python3 -m http.server`), then open `/docs/`. It reads the local `agent-status/*.json`, auto-refreshes, and flags file conflicts. (No GitHub fetch — `git pull` to see teammates' latest.)

**Before you start, and every ~30 min:**

1. `git pull origin main`.
2. **Check the dashboard** (or read the other two `agent-status/agent-*.json`). **Do not touch a file another agent has claimed** in their `files` list — coordinate first.
3. **Claim your work** in your own status file — Melody → `agent-status/agent-melody.json`, Nuha → `agent-nuha.json`, Tony → `agent-tony.json`:
   ```json
   { "agent": "Melody", "status": "working", "currentTask": "short description",
     "files": ["paths you'll touch"], "blockers": [], "waitingOn": null,
     "lastUpdated": "ISO timestamp", "notes": "" }
   ```
   Then push immediately:
   ```bash
   git add agent-status/agent-<yours>.json
   git commit -m "[status] <name>: <what you're doing>"
   git push
   ```
4. **When done:** set `status` to `idle`, clear `currentTask` and `files`, push.

**Rules:** only edit your own status file and your own lane's files; always `git pull` before starting new work.
