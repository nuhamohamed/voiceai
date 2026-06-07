# Standup Proxy

When a teammate misses standup, their **AI clone** joins in their cloned voice and answers questions about their work — grounded in their real context (Linear / Slack) pulled live from **Moss** — then posts a Slack summary.

Built at the Moss Conversational AI Hackathon. **Python + LiveKit.**

## Who's building what

| Person | Owns |
|--------|------|
| **Melody** | Person A's context → a corpus file |
| **Nuha** | Moss retrieval + voice cloning |
| **Tony** | the LiveKit agent + room + Slack summary |

Full briefs are in **`prds/`** (start with `prds/README.md`). Your paste-into-your-agent kickoff is in **`prds/handoffs/`**.

## Working together

Read **`CLAUDE.md`**. Before you code: `git pull`, claim your task in `agent-status/<you>.json`, and only touch your own lane's files.

**Status dashboard:** serve from the repo root and open `/docs/`:

```bash
python3 -m http.server
# then open http://localhost:8000/docs/
```
