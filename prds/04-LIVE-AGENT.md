# PRD 04 — Live: the Agent + Room (LiveKit)

**Owner:** Tony · **Roadmap:** Phase 4 · **Requirements:** LIV-01..04
**Calls:** Nuha's `retrieve()` + Nuha's voice config. **The demo runs in your code.**
**How (source-verified):** see `prds/04-LIVE-AGENT-DESIGN.md` — phased plan, exact APIs, decisions.

## Mission

Build **the agent** — the LiveKit thing that joins the standup, listens, takes turns, and speaks as Person A's clone. On a follow-up: call `retrieve()`, inject the context, let the LLM answer, speak it in A's voice, and **show the 🔎 Moss → chunk on screen**. On adjourn: post a **Slack summary**. You assemble everyone's pieces into the demo.

## What you build

1. **LIV-01** A LiveKit `AgentSession` + room with real-time turn-taking, demoable in the **LiveKit playground**.
2. **LIV-02** The clone joins and delivers Person A's update in cloned voice.
3. **LIV-03** The follow-up flow via Moss's official hook:
   ```python
   async def on_user_turn_completed(self, turn_ctx, new_message):
       chunks = await retrieve(new_message.text_content, persona_id)  # Nuha's function
       turn_ctx.add_message(role="assistant", content=format(chunks)) # inject A's real context
       # ^ LiveKit RAG docs use role="assistant" (Moss page shows "system"); see design spec
       # LLM answers; voice = cached clone WAV (Phase 1) / Qwen tts_node (Phase 2) — NOT a 1-line plugin
       show_trace(chunks)   # 🔎 Moss → ref  (the visible moat)
   ```
4. **LIV-04** On adjourn → summarize the standup → post action items to a **Slack** channel.

## Scope

**In:** the room, turn-taking, the `on_user_turn_completed` wiring, the LLM plugin, plugging in Nuha's voice, the on-screen trace, the Slack summary, running the 2-min script. **Out:** how Moss finds chunks (Nuha), how the voice is cloned (Nuha), the content (Melody). You **assemble**, you don't build those internals.

## Success criteria

1. A multi-party voice room runs via LiveKit Agents with turn-taking, in the playground.
2. The clone joins and gives A's update in cloned voice.
3. The scripted follow-up runs end-to-end: question → `retrieve()` → visible 🔎 trace → spoken grounded answer.
4. On adjourn, a summary with action items posts to Slack.

## How to not wait on anyone

You also do **Foundation** first (`00`), so you start with your own stubs. Build the whole room against the **`retrieve()` stub** + a **placeholder voice** + the **sample corpus**. Swap in the real `retrieve()` (Nuha) and real voice (Nuha) when ready — one line each. You're never blocked.

## Design decisions that are yours

- Turn-taking / who-speaks-when for the scripted exchange (LiveKit's turn detection handles agent↔human automatically — lean on it).
- How the 🔎 retrieval trace appears in the playground (this is the *visible* moat — make sure judges see context→answer, not just hear it).
- Summary format + Slack channel/webhook; what counts as an action item.
- Whether the PM is a human (simplest) or a manager-clone (bonus, if time).

## SDKs you touch

**LiveKit Agents (Python)** — `AgentSession`, rooms, `on_user_turn_completed`, turn detection · an **LLM plugin** (OpenAI/TrueFoundry) · **Slack** webhook. Plug in Nuha's TTS for voice. **Ground every LiveKit call in the `livekit-docs` MCP + the Moss×LiveKit page** — don't hallucinate the Agents API.

## Next

`/gsd-plan-phase 1` (Foundation) then `/gsd-plan-phase 4`, or build from the list. **Restart Claude Code first.**
