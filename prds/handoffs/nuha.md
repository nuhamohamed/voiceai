<!-- Paste everything below into Nuha's Claude Code agent (in the team repo nuhamohamed/voiceai). -->

You're helping **Nuha** build her two lanes of the **Standup Proxy** hackathon project (Moss Conversational AI Hackathon, ~24h, Python + LiveKit).

**Product (one line):** when a teammate is absent from standup, their AI clone joins in their cloned voice and answers questions about their work — grounded in that person's real context retrieved live from **Moss** — then posts a Slack summary. The killer moment: the clone answers a follow-up with the *right, real specifics* from Moss, shown on screen and spoken in the person's voice.

## Your two lanes

**Lane 1 — Moss retrieval (the moat's engine).** PRD: `prds/02-MOSS-RETRIEVAL.md`.
Load Person A's corpus into Moss and build the one function that finds the right context.
- **Outcome:** `async retrieve(query_text, persona_id) -> list[RetrievedChunk]` (each `{text, source, ref, score}`) that makes the scripted demo follow-up return the **correct specific chunk** — provable in plain text, no room/voice. Hand it to Tony.
- **Interfaces:** in = Melody's corpus file; out = the `retrieve()` signature above (Tony calls it; `ref` flows to the on-screen trace).

**Lane 2 — Voice.** PRD: `prds/03-VOICE.md`.
Make the clone sound like Person A + turn spoken questions into text.
- **Outcome:** Person A's cloned voice with the **scripted lines pre-rendered** (always works) + an STT config. Hand to Tony.
- **Verified reality (don't rediscover):** a Qwen-cloned voice does **not** plug into a LiveKit TTS slot. Use **offline Qwen clone → pre-render the scripted lines** (recommended; Qwen sponsor credit; no paid plan). Optional live clone = **LiveKit Custom Voices** (`v_*` id → `tts="cartesia/sonic-3:v_…"`) — needs a **paid LiveKit Ship plan**, uses Cartesia/Inworld, not Qwen. Stock plugin voice (MiniMax/OpenAI) for unscripted speech; Deepgram (or similar) for STT. The MiniMax LiveKit plugin can't clone.

## Sequencing
Voice is **independent and lighter** — knock out the offline clone + pre-rendered lines first. Then build Moss retrieval against `data/sample_corpus.jsonl` (Tony ships it in Foundation) until Melody's real corpus lands; swap it in later with no code change. If Foundation isn't pushed yet, you can still start Voice immediately and use a tiny sample corpus you make yourself for Moss.

## First steps
1. **Read both PRDs:** `prds/02-MOSS-RETRIEVAL.md` and `prds/03-VOICE.md`.
2. **Coordination protocol** (in `CLAUDE.md`): you're **Agent C** → update `agent-status/agent-c.json`. `git pull`, claim your work, commit+push with a `[status]` prefix, re-pull every ~30 min.
3. **Build:** start with the Voice clone + cached lines, then Moss retrieval.

## Rules
- **Only touch your lanes:** the retrieval code and the voice code/audio. Do **not** edit Melody's corpus content, Tony's LiveKit agent/room, or the dashboard.
- **Source-driven:** ground every Moss / LiveKit / Qwen call in current docs — the Moss × LiveKit page and the `livekit-docs` MCP. Don't guess API names.
- The moat is live **retrieval**, not live **TTS** — cached cloned audio for the scripted lines is enough for the wow. Don't over-invest in live cloning.

Start by reading both PRDs, claim your status, then build Voice first.
