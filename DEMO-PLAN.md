# CloneAgent — Hackathon Build Plan (one-pager)

**One line:** a context-faithful AI clone that joins a meeting you can't make, asks the *exact* question **you** would ask (because it has your real context), and briefs you after. Demoed for one double-booked employee; framed as the bottoms-up wedge into enterprise.

> Integrity line: demo only what's *real*; pitch enterprise as *vision*. The live demo genuinely works; "ingests your whole org" is roadmap.

---

## North star: the demo decides everything — build backward from it.

### 2-minute demo script
- **0:00–0:20 — Hook (one person, acute pain):** "I'm an engineer at a startup, double-booked *right now* — sprint planning **and** an architecture/vendor call at the same time. Can't be in both… so I cloned myself."
- **0:20–0:45 — The clone's brain:** show it holds *my* context — current project, recent decisions, what I care about. Start the meeting (transcript/audio).
- **0:45–1:45 — WOW (the moat, made visible):** a topic I care about comes up → on screen the clone **retrieves my context** (e.g. *"pulled: we chose Postgres last week; I care about the latency budget"*) → then asks the **exact question I'd ask**, in my cloned voice. The judge SEES context → question.
- **1:45–2:00 — Report-back + close:** clone briefs me — *"here's what happened, the 1 decision that needs you, the question I asked on your behalf."* Close: buyer = employees/teams; why-now = voice clone + real-time retrieval just crossed the line; vision = every employee's clone (the hard part — composing org context — is our wedge).

---

## Build ladder — bottom-up, ALWAYS demo-able
1. **SPINE (build FIRST — deps: Moss + LLM + a transcript):** hardcode a thin slice of "my context" → index in Moss. Feed a meeting transcript. At a trigger (topic I care about), retrieve context → generate **the specific question I'd ask** + the **report-back**. **Text on screen is fine.** Proves the magic. **Render the context→question link on screen.**
2. **VOICE (big wow):** speak the question + report in my cloned voice (Minimax / Qwen).
3. **LIVE (most fragile — only if time):** LiveKit room, two-way audio, live transcription, clone speaks at the right moment.

**Defer LiveKit, voice-clone, and Unsiloed (hardcode the context). Each is a LAYER, not a prerequisite. Do NOT start with meeting plumbing.**

## Go / no-go checkpoint
If the spine (right question from real context) isn't landing after the first build block → ship **report-back-only** (same idea, far simpler) and stop chasing live audio.

## Sponsor mapping
**Moss** = live context retrieval (core) · **Minimax/Qwen** = cloned voice · **LiveKit** = live meeting audio · **Unsiloed** = ingest context (later) · **TrueFoundry** = LLM gateway (optional, demo insurance).

## Stack
TypeScript (strict) / Node. Moss `@inferedge/moss`. LLM via TrueFoundry gateway or direct.

## Setup needed (tonight, before deep build)
- [ ] Node + TS project scaffolded
- [ ] Moss account + key (`@inferedge/moss`)
- [ ] An LLM key (TrueFoundry gateway, or direct)
- [ ] (later) Minimax/Qwen voice-clone key · LiveKit Build-plan key
