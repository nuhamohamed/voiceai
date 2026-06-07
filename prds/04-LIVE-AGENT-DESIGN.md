# PRD-04 Design Spec — Live Agent (LiveKit)

**Owner:** Tony · **Branch:** `feat/tony-live-agent` · **Elaborates:** `prds/04-LIVE-AGENT.md`
**Approach:** **fork-and-adapt** the official `moss-hacker-starter` (LiveKit + Moss), not build from scratch.
**Status:** design approved; ready for implementation plan.

Every framework call is verified against current LiveKit docs + the starter's real source
(see [Sources](#sources)) — source-driven, because the LiveKit Agents API has shifted
(`AgentServer` replaced `WorkerOptions`).

---

## 1. Goal & the moat

Person A's clone joins a LiveKit voice room, gives the standup update, and **answers a live
follow-up grounded in real context**, with the retrieved source **shown on screen as it speaks**.
The moat moment (must land in the video): PM asks the follow-up → the screen's source panel shows
the *real* retrieved chunk (e.g. `ENG-419 Refresh-token rotation`) → the clone speaks the grounded
answer. Context + answer, on screen and spoken, together.

Slack summary (LIV-04) is **deferred** — out of immediate scope per team call; it's a ~10-line
webhook to bolt on last.

## 2. Why fork the starter

`moss-hacker-starter` is ~80% of this product and **already implements the hardest part of the
moat**: a Next.js frontend "Knowledge Matches" panel that renders retrieved chunks + scores in real
time, fed by the agent's `moss_context` data packets. We adopt it and adapt it to our content.

| Starter piece | Verdict |
|---|---|
| `AgentServer` + `@server.rtc_session` + `AgentSession` (inference STT=deepgram, VAD, turn detection, noise cancel) | **KEEP** |
| Frontend panel + `_publish_moss_context()` → `moss_context` packet → `useMossContextEvents` hook | **KEEP** — this is our 🔎 trace |
| `MossClient.query` / `create_index.py` code | **HAND TO NUHA** — it's her Lane-1 Moss work |
| `search_knowledge` tool (LLM calls it, grounds answer) | **ADAPT** → call our `retrieve()` instead of the starter's own Moss |
| Persona instructions ("LiveKit docs helper") | **ADAPT** → Person A's standup clone (`personas.system_prompt`) |
| Opening greeting (`generate_reply`) | **ADAPT** → standup update (play `audio/demo/update.wav`) |
| `inference.TTS(cartesia)` generic voice | **ADAPT** → clone voice (the one real swap) |
| `remember_fact` / `recall_facts` + memory index + per-user cookie | **DROP** — not needed for the standup proxy |

## 3. Lane boundary (stays in PRD-04)

The decisive choice that keeps this in-lane: **wire `search_knowledge` → `retrieve()`**, ignoring the
starter's built-in Moss code. We *consume* others' seams; we don't *edit* their files.

| | What |
|---|---|
| **CREATE (new, mine)** | `agent-py/` (the agent) + `frontend/` (the panel), adapted from the starter |
| **CONSUME (call, don't edit)** | `brain.retrieval.retrieve()`, `personas.get_persona()`, `voice.config`, `audio/demo/*.wav`, `data/person_a_corpus.jsonl` |
| **DON'T TOUCH** | `brain/retrieval.py` internals (Nuha), `voice/*.py` (Nuha), `data/*` (Melody), `prds/01-03` |
| **Housekeeping only** | append starter ignores to `.gitignore`; add root `package.json` orchestrator |

**The 3 fixed interfaces are unchanged** — we only call `retrieve()`, read the corpus, and read the
voice config. No shared-interface edits (CLAUDE.md compliant). One *non-edit* coordination: a
heads-up to Nuha that the agent calls `retrieve()`, so her Moss lands behind it.

## 4. Architecture — the adapted flow

```
Browser frontend (Next.js)  ──WebRTC──▶  LiveKit Cloud (media + Inference STT/LLM/TTS)
   • mic / audio                                    │ dispatch
   • 🔎 Source panel  ◀── moss_context data ───┐    ▼
                                               │  agent-py (AgentServer)
PM asks follow-up (spoken)                     │   • on_enter → play update.wav (standup update)
   └─ Deepgram STT → text                      │   • search_knowledge tool:
       └─ LLM calls search_knowledge ──────────┘        chunks = await retrieve(query, "person_a")  ← our seam
                                                         publish_moss_context(chunks)  → 🔎 panel
                                                         return chunks → LLM grounds the answer
                                                    • answer spoken in CLONE voice
```

- **Retrieval:** `search_knowledge` calls `retrieve(query, persona.id)` → `list[RetrievedChunk]`.
  We format chunks for both the LLM (grounding) and the `moss_context` packet (the panel). Nuha's
  Moss sits behind `retrieve()`; today it's the keyword stub — identical interface.
- **The panel** is the starter's, fed our chunks (adapt `_publish_moss_context` to read
  `RetrievedChunk{text, source, ref, score}` instead of raw Moss docs).
- **Import bridge:** `agent-py` reaches our root seams via a `sys.path` insert to the repo root
  (same pattern as `scripts/harness.py`), so `from brain.retrieval import retrieve` works.

## 5. Voice (the one real adaptation)

The starter speaks with generic `inference.TTS(cartesia)`. We want the clone. Sequence it:

- **Step A — prove the pipeline (fastest):** run the starter as-is with our corpus + persona.
  Live grounded answer + on-screen panel, generic voice. Confirms the moat end-to-end.
- **Step B — clone voice:** swap the voice. Options, decided at that task:
  - **cached Qwen WAVs** (`audio/demo/{update,blocker}.wav`, already rendered) — play the matching
    clip for the scripted demo answers; clone voice, zero new infra.
  - **Qwen `tts_node`** — live clone voice via Nuha's `synthesize()` → `rtc.AudioFrame`s (reuses
    enrollment, non-streaming latency on short answers).
  - **ElevenLabs plugin** — one-line `tts=elevenlabs.TTS(voice_id=…)`, live + streaming + clone,
    needs an ElevenLabs key + re-clone.

## 6. Key decisions (verified)

| Decision | Choice | Source |
|---|---|---|
| Base | fork `moss-hacker-starter` | starter README |
| Bootstrap | `AgentServer` + `@server.rtc_session` + `cli.run_app(server)` | voice-ai, starter agent.py |
| Models | LiveKit Inference (STT `deepgram/nova-3`, LLM `openai/...`) — no extra keys | starter agent.py |
| RAG | tool-call `search_knowledge` → **our `retrieve()`** (not starter's Moss) | external-data, lane rule |
| Trace | starter's `moss_context` packet → frontend panel (= 🔎 card), fed our chunks | starter agent.py + hook |
| Opening update | play `audio/demo/update.wav` on enter (cached clone voice) | playing_audio recipe |
| Answer voice | generic first → clone (Step B) | this spec §5 |
| Creds | LiveKit (set ✅) + Moss (Nuha) only; redeem `HACK-MOSS-YC` for inference credits | hackathon page |
| Slack | deferred | team call |

## 7. Success criteria (PRD-04 LIV-01..03; LIV-04 deferred)

1. **LIV-01** Voice room runs via LiveKit Agents with turn-taking (frontend or `console`).
2. **LIV-02** Clone joins and delivers Person A's update in cloned voice (`update.wav`).
3. **LIV-03** Live follow-up end-to-end: spoken question → `retrieve()` → visible 🔎 panel →
   grounded answer, spoken in clone voice. ← the moat
4. *(deferred)* **LIV-04** Slack summary on adjourn.

## 8. Build order & risks

Order (so something always works): **(1)** pull starter + creds → it runs as the docs-helper;
**(2)** swap corpus + persona + `search_knowledge → retrieve()` → grounded on OUR content, panel
shows our chunks (generic voice); **(3)** opening update = `update.wav`; **(4)** clone voice (Step B);
**(5)** record. Frontend after the agent works (console is the fallback surface).

- **Frontend (Node/pnpm) setup painful** → demo via `console` + the panel later; agent still proves LIV-03.
- **Real Moss not ready** → stub `retrieve()` is identical; flow + panel unaffected.
- **Clone-voice swap slips** → generic voice + on-screen trace still carries the moat (Step A).
- **Demo floor:** LIV-03 (live retrieve → visible panel → spoken grounded answer) must work.

## Sources

- Starter (structure, agent.py, create_index.py): https://github.com/livekit-examples/moss-hacker-starter
- voice-ai quickstart: https://docs.livekit.io/agents/start/voice-ai
- Pipeline nodes & hooks (`StopResponse`, `tts_node`): https://docs.livekit.io/agents/logic/nodes
- External data & RAG (tool-call vs hook, inject role): https://docs.livekit.io/agents/logic/external-data
- Playing Audio (`session.say(text, audio=…)`, WAV→`AudioFrame`): https://docs.livekit.io/reference/recipes/playing_audio
- ElevenLabs TTS (clone via plugin+key): https://docs.livekit.io/agents/models/tts/elevenlabs
- Hackathon (creds, `HACK-MOSS-YC`, starter): https://www.livekit.info/conversational-ai-hackathon
- Moss × LiveKit (query shape, `role="system"` conflict): https://www.moss.dev/integrations/livekit
