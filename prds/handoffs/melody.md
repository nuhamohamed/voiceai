<!-- Paste everything below into Melody's Claude Code agent (in the team repo nuhamohamed/voiceai). -->

You're helping **Melody** build her lane of the **Standup Proxy** hackathon project (Moss Conversational AI Hackathon, ~24h, Python + LiveKit).

**Product (one line):** when a teammate is absent from standup, their AI clone joins in their cloned voice and answers questions about their work — grounded in that person's real context retrieved live from **Moss** — then posts a Slack summary. The killer moment: the clone answers a follow-up with the *right, real specifics* pulled from Moss, shown on screen and spoken in the person's voice.

## Your lane: Person A's memory — the content

You author Person A's real work context and export it as a corpus file. **Your content is the moat** — if the clone's answer sounds real and specific, it's because your content held the specifics.

**Your outcome (the one thing you deliver):** a valid `data/person_a_corpus.jsonl`, rich and specific enough that retrieval can answer the auth-migration follow-up with true, concrete detail. You hand this file to Nuha — nothing else.

**The interface you must honor** — one JSON record per line:
```json
{"id": "lin-eng-412", "source": "linear|slack|calendar", "ref": "ENG-412 Auth migration", "text": "..."}
```
`ref` shows on screen in the retrieval trace, so keep it human-readable. The format is the only fixed thing — *how* you create the content (Linear UI, Linear API, by hand) is entirely yours.

## First steps
1. **Read your full PRD:** `prds/01-LINEAR-CONTENT.md` — it has your outcome, the interface, and what "done" looks like.
2. **Coordination protocol** (in `CLAUDE.md`): `git pull`, then claim your work in your status file `agent-status/agent-<you>.json` and commit+push with a `[status]` prefix. (Nuha is **Agent C**; you're **Agent A** — confirm your letter with the team since the protocol only fixes Nuha.) Re-pull every ~30 min.
3. **Build:** author Person A's auth-migration ticket + a few related notes (status, what's done, the specific blocker), export to the corpus file. Ship an **early draft fast** — you're the unblocker, Nuha can't load Moss until a first version exists — then enrich.

## Rules
- **Only touch your lane:** the corpus file (and any export script you write). Do **not** edit the retrieval/voice/agent code, the dashboard, or anyone else's status file.
- **Source-driven:** if you use the Linear API, ground every call in current Linear docs — don't guess endpoints.
- Short, **one-fact-per-record** entries retrieve better than long multi-topic ones.

Start by reading `prds/01-LINEAR-CONTENT.md`, claim your status, then build.
