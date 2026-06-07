# Standup Proxy

When a teammate misses standup, their **AI clone** joins in their cloned voice and answers questions about their work, grounded in their real context (Linear / Slack) pulled live from **Moss**, then posts a Slack summary.

Built at the Moss Conversational AI Hackathon. **Python + LiveKit.**

## How it works

```mermaid
flowchart TB
    src["Linear / Slack / calendar<br/>Nuha's real work"]
    corpus["data/person_a_corpus.jsonl<br/>id, source, ref, text"]
    moss[("Moss index<br/>per persona")]

    src -->|authored and pulled| corpus
    corpus -->|ingested| moss

    subgraph room["Live standup in a LiveKit room"]
        pm["PM asks a question (spoken)"]
        stt["Deepgram STT: speech to text"]
        ret["retrieve(query, persona) returns chunks<br/>the shared contract"]
        ans["Grounded answer,<br/>spoken in the cloned voice"]
        trace["Moss source shown on screen<br/>ref, source, relevance"]
        pm --> stt --> ret
        ret --> ans
        ret --> trace
    end

    moss -.->|queried live| ret
    ans --> adj["On adjourn"]
    adj --> slack["Slack summary and action items"]
```

The moat is `retrieve()` pulling the **right real chunk** live, shown on screen *and* spoken in the cloned voice.

## Run the demo

The live agent (`agent-py/`) and the on-screen trace panel (`frontend/`) are built on the official LiveKit + Moss starter. Two sets of credentials: **LiveKit** in `agent-py/.env.local` and **Moss** in `.env`.

```bash
# 1. Build the persona's Moss index from the corpus (once, or whenever the corpus changes)
uv run --project agent-py python -m brain.ingest

# 2. Run the agent + frontend together
pnpm dev      # open http://localhost:3000, click "Start call", allow the mic
```

In the call, ask **"What's the status of the auth migration?"**, then **"What's actually blocking it?"**. The clone answers in its cloned voice while the retrieved Moss chunks light up on screen (ref, source, relevance).

**Quick checks** (no room or voice, just the retrieval seam plus tests):

```bash
uv run --project agent-py python scripts/harness.py "what's blocking the auth migration?"
uv --directory agent-py run pytest -q     # grounding + integration tests (12)
```

New here? Read your PRD in `prds/` (live-agent detail in `prds/04-LIVE-AGENT-*.md`).

## Working together

Read **`CLAUDE.md`**. Before you code: `git pull`, claim your task in `agent-status/<you>.json`, and only touch your own lane's files.

**Status dashboard:** serve from the repo root and open `/docs/`:

```bash
python3 -m http.server
# then open http://localhost:8000/docs/
```
