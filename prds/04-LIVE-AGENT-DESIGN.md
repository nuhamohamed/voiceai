# PRD-04 Design Spec — Live Agent (LiveKit)

**Owner:** Tony · **Branch:** `feat/tony-live-agent` · **Elaborates:** `prds/04-LIVE-AGENT.md`
**Status:** design approved in brainstorming; ready for implementation plan.

This is the *how* for PRD-04. Every framework call below is verified against current
LiveKit docs (see [Sources](#sources)) — source-driven, not from memory, because the
LiveKit Agents API has shifted (e.g. `AgentServer` replaced the old `WorkerOptions`).

---

## 1. Goal & the moat

Assemble everyone's pieces into the demo: a LiveKit voice room where Person A's clone
gives a standup update and **answers a live follow-up grounded in real context**, with the
retrieved source **shown on screen as it speaks**. On adjourn, post a Slack summary.

**The moat, concretely (what the video must show):** the PM asks a follow-up; the screen
shows `🔎 Moss → ENG-419 Refresh-token rotation` (the *real* retrieved chunk); the clone
speaks the matching grounded answer in its cloned voice — context and answer, on screen and
spoken, at the same moment.

## 2. Two-phase plan

We ship in two phases so a complete, honest demo video exists early, then gets more "real".

| | Phase 1 — records the demo video | Phase 2 — the interactive/real version |
|---|---|---|
| Question in | Deepgram STT (live) | same |
| Retrieval | **live `retrieve()`** → drives the on-screen 🔎 trace | same (real Moss behind it) |
| Spoken answer | **play cached clone-voice WAV** (`audio/demo/*.wav`) | **live LLM answer** through a **Qwen `tts_node`** |
| Voice on the answer | clone voice (pre-rendered) | clone voice (live) |
| Opening update | play `update.wav` on enter | same, or live |
| Slack | POST summary on adjourn | same |

**Why cached answers in Phase 1 (the key decision):** the deliverable is a *recorded video*,
so there is no live off-script risk. Nuha already cached the answers **in the clone voice**,
so playing them gives us clone-voice on the moat moment with **zero `tts_node` work**, while
**retrieval stays genuinely live on screen**. The only thing pre-rendered is the TTS; the
proof (Moss pulling the real chunk) is real. Phase 2 swaps cached playback for a live LLM
answer voiced through the Qwen clone — and **nothing from Phase 1 is thrown away** (room, STT,
live `retrieve()`+trace, Slack all carry over; only the answer's source changes).

## 3. Seams I consume (do NOT edit — other lanes own these)

```python
from brain.retrieval import retrieve, RetrievedChunk   # Nuha — currently a stub, real Moss incoming
from personas import get_persona                        # shared — persona.voice_id, .system_prompt, .id, .moss_index
from voice.config import STT_PLUGIN, AUDIO_CACHE_DIR     # Nuha — "deepgram", "audio/demo"
```

- `retrieve(query_text, persona_id) -> list[RetrievedChunk]` where each chunk is
  `{text, source, ref, score}`. I call it; I never call Moss directly.
- Cached answers: `audio/demo/{update,blocker,slack_summary}.wav` — **clone-voice WAV**.
- **Dependency / blocker:** the `*.wav` files are not in the repo (Nuha has them locally).
  Phase 1 playback needs them — either Nuha commits them, or I regenerate with
  `python -m voice.cache_demo_lines` (needs `DASHSCOPE_API_KEY`). Tracked in my status `waitingOn`.

I build against the **stub `retrieve()`** + a **placeholder TTS** until real ones land, so I'm
never blocked (per PRD-04 "how to not wait on anyone").

## 4. Architecture — the Phase-1 live flow

```
Clone joins room
   └─ on_enter: session.say(update_text, audio=update.wav)      ← opening standup update (cached, clone voice)

PM asks follow-up (spoken)
   └─ Deepgram STT → text
       └─ on_user_turn_completed(turn_ctx, new_message):        ← the hook (LiveKit drives turn-taking)
            1. chunks = await retrieve(new_message.text_content, persona.id)   ← LIVE retrieval
            2. publish_trace(chunks)        → 🔎 Source card on screen (the visible moat)
            3. answer = route(new_message.text_content)          → which cached WAV (e.g. blocker.wav)
            4. await session.say(answer_text, audio=blocker.wav) → spoken grounded answer (clone voice)
            5. raise StopResponse()         → suppress the default LLM reply (Phase 1 only)

On adjourn
   └─ POST slack_summary text to Slack incoming webhook
```

**Mechanism note (the linchpin to validate first):** steps 4–5 — playing a cached answer and
suppressing the LLM's own reply — are the one non-obvious bit. `session.say(text, audio=gen)`
is documented (Playing Audio recipe) and `raise StopResponse()` inside `on_user_turn_completed`
is documented (nodes hook). The exact interplay (say-then-StopResponse ordering) is the first
thing to prove in a spike before building the rest.

**Phase-2 mechanism:** delete steps 3–5; let the pipeline run — inject chunks
(`turn_ctx.add_message(role="assistant", content=format(chunks))`), the LLM answers, and a
custom `tts_node` routes that text through Nuha's `synthesize()` (Qwen) → `rtc.AudioFrame`s.

## 5. Files I create (new `agent/` package — my lane)

```
agent/
  __init__.py
  main.py          # AgentServer + @server.rtc_session entrypoint + AgentSession wiring + cli.run_app
  clone_agent.py   # Agent subclass: on_enter (play update), on_user_turn_completed (retrieve→trace→say→stop)
  trace.py         # publish_trace(chunks): push the 🔎 source to the frontend (text-stream / RPC)
  playback.py      # load_wav(path) -> async gen of rtc.AudioFrame  (stdlib `wave`)
  routing.py       # route(question) -> cached answer key  (intent/keyword, with a default)
  slack.py         # post_summary(text): POST to SLACK_WEBHOOK_URL
frontend/          # Phase-1-B: minimal custom page rendering the Source card (agent-starter-react)
```

Plus small edits to files I own: `prds/04-LIVE-AGENT.md` (corrections), `requirements.txt`
(uncomment + pin the verified LiveKit deps — done at build time with rationale in the commit).

## 6. Key decisions (verified, with rationale)

| Decision | Choice | Why / source |
|---|---|---|
| Worker bootstrap | `AgentServer()` + `@server.rtc_session(...)` + `cli.run_app(server)` | current API; **not** the old `WorkerOptions` — would break against the SDK. [voice-ai] |
| STT | Deepgram (`STT_PLUGIN`), `inference.STT("deepgram/nova-3")` placeholder | Nuha's config + verified default. [voice-ai] |
| Turn-taking | `silero.VAD` + `MultilingualModel()` turn detection, prewarmed via `server.setup_fnc` | LiveKit handles agent↔human turns automatically. [voice-ai, playing_audio] |
| Answer (P1) | play cached clone-voice WAV via `session.say(text, audio=…)`, then `StopResponse()` | clone voice + reliable for a recorded video; retrieval stays live. [playing_audio, nodes] |
| Answer (P2) | live LLM, inject chunks `role="assistant"`, voice via Qwen `tts_node` | documented RAG pattern; ⚠ see role conflict below. [external-data, nodes] |
| Inject role | `assistant` (LiveKit-documented), **not** `system` | ⚠ Moss×LiveKit page uses `system`; LiveKit RAG docs use `assistant`. `assistant` framing tends to yield more natural first-person grounded answers. Trivial to flip. [external-data vs moss.dev] |
| LLM | `inference.LLM("openai/...")` now; TrueFoundry via OpenAI-compatible plugin later | no keys for placeholder; sponsor credit path is `openai.LLM()` compatible endpoint. [openai-llm] |
| Trace surface | **hybrid**: A) `lk.chat` text line first → B) custom Source card | recorded video → the on-screen context→answer IS the payoff, so prioritize the card. [text, external-data] |
| Cached file format | WAV (stdlib `wave` → `AudioFrame`) | Nuha shipped WAV; no decode dependency. [playing_audio] |

## 7. The 🔎 trace surface (hybrid A → B)

The Agent Console shows only the `lk.transcription` / `lk.chat` streams. A distinct **Source
card** (ref + source badge + chunk text, lit up as the clone speaks) needs a custom frontend
reading a custom text-stream topic or an RPC from the agent.

- **A (safety net, build first):** push `🔎 Moss → {ref}` as an `lk.chat` text line. Zero
  frontend. Always demoable.
- **B (the win, prioritized for the video):** `agent-starter-react` page that renders the
  Source card from a trace message. `trace.py` is the single seam, so A→B is a swap of how the
  trace is delivered, not a rewrite.

## 8. Slack summary

On adjourn, POST the `slack_summary` text to a Slack **incoming webhook** (`SLACK_WEBHOOK_URL`
in `.env`). Plain HTTP, no SDK-version risk. "Adjourn" trigger = session close / a `/done`
command (decide in plan). Action items = the lines already in `slack_summary`.

## 9. Success criteria (maps to PRD-04 LIV-01..04)

1. **LIV-01** Multi-party voice room runs via LiveKit Agents with turn-taking (Agent Console).
2. **LIV-02** Clone joins and delivers Person A's update in cloned voice (cached `update.wav`).
3. **LIV-03** Scripted follow-up runs end-to-end: spoken question → **live `retrieve()`** →
   visible 🔎 trace → grounded answer spoken in clone voice. ← the moat
4. **LIV-04** On adjourn, a summary with action items posts to Slack.

## 10. Risks & fallback ladder

- **Cached WAVs missing** → regenerate via `voice.cache_demo_lines` (needs `DASHSCOPE_API_KEY`),
  else placeholder TTS so the flow still runs.
- **`say`+`StopResponse` interplay misbehaves** → fall back to generic streaming `inference.TTS`
  for the answer and lean on the on-screen trace (Phase-1.5).
- **Custom frontend (B) not ready** → ship surface A (trace as chat line). Demo still lands.
- **Real Moss not ready** → keep stub `retrieve()`; the trace + flow are identical.
- **Floor of the demo:** even if everything else slips, LIV-03 (live retrieve → visible trace →
  spoken answer) must work. That one moment is the product.

## 11. Deferred to Phase 2 (out of scope for the video)

- Live LLM-generated answers + Qwen `tts_node` (clone voice on live generation).
- Real Moss behind `retrieve()` (Nuha's Lane 1, in progress).
- Manager-clone PM (bonus). PM is a human asking the question in Phase 1.

## Sources

- voice-ai quickstart (AgentServer, AgentSession, STT/LLM/TTS, cli.run_app): https://docs.livekit.io/agents/start/voice-ai
- Pipeline nodes & hooks (`on_user_turn_completed`, `StopResponse`, `tts_node`): https://docs.livekit.io/agents/logic/nodes
- External data & RAG (inject pattern, `role`, frontend RPC): https://docs.livekit.io/agents/logic/external-data
- Text & transcriptions (text streams, `lk.chat`, frontend rendering): https://docs.livekit.io/agents/build/text
- Playing Audio recipe (`session.say(text, audio=…)`, WAV→`AudioFrame`): https://docs.livekit.io/reference/recipes/playing_audio
- OpenAI LLM (inference vs plugin, OpenAI-compatible/TrueFoundry path): https://docs.livekit.io/agents/models/llm/openai
- ElevenLabs TTS (verified alternative; cloning needs plugin+key): https://docs.livekit.io/agents/models/tts/elevenlabs
- Moss × LiveKit (retrieve/query shape, `role="system"` — the conflict): https://www.moss.dev/integrations/livekit
