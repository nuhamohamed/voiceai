# Standup Proxy (Clone Agent)

## What This Is

A *standup proxy*: when a teammate can't attend standup, **their clone agent joins in their cloned voice**, gives their update, and **answers follow-up questions about their work in real time** — grounded in that person's week of context (Slack / calendar / Linear) retrieved live via **Moss** — then posts action items to a Slack summary channel. Built for the Moss-hosted Conversational AI Hackathon (YC SF, Co-Pilot track). Buyer = teams and managers losing hours to status meetings. The hackathon demo uses 2 hardcoded personas (the team members themselves).

## Core Value

**The clone answers a live follow-up question with the *right, real specifics* retrieved from that person's context in Moss** — visibly (retrieval shown on screen) and audibly (in their cloned voice). If everything else fails, this one moment must work — it is the moat and the demo's killer moment.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. Hypotheses until shipped. -->

- [ ] Per-user context ingestion: Slack / calendar / Linear export → chunked → indexed in Moss under a per-user namespace
- [ ] `handleTurn(incomingText) -> { responseText }` brain: retrieve from Moss (user namespace) → LLM → grounded answer, callable from BOTH a text harness and the live voice loop
- [ ] Retrieval is made **visible** (e.g. `🔎 Moss → [chunk used]`) so judges see the moat, not just hear it
- [ ] Text-mode build + iteration path (print response) before any voice/room plumbing
- [ ] Voice mode: STT → `handleTurn` → TTS in the absent teammate's **cloned voice** (Qwen; Minimax TTS fallback)
- [ ] Pre-cached exact demo lines as a day-of safety net for the voice layer
- [ ] Live multi-party voice room via LiveKit Agents with real-time turn-taking
- [ ] One clean **manager-clone → teammate-clone** exchange (the asker is the manager's clone — one purposeful agent→agent moment)
- [ ] On adjourn: summarize the standup → post action items to a Slack summary channel
- [ ] 2 hardcoded personas (the team members) with cloned voice + system prompt each
- [ ] Go/no-go fallback path: if the spine doesn't land after the first build block, ship **Slack-summary-only** (same idea, simpler)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Full company brain / org-wide context composition — vision only; the hard part, pitched as the wedge, not built today
- Slack OAuth / multi-tenant auth — hackathon uses hardcoded personas; auth is post-hackathon
- Autonomous agent-to-agent chatter (clones freely conversing) — team cut it; demo only ONE scripted manager→teammate exchange, pitch the rest as vision
- Screen / OS watching — not core to the standup-proxy value, time sink
- Custom UI / web frontend — demo runs in the **LiveKit playground** + a Slack channel; no bespoke UI
- TypeScript — the team is building in Python (LiveKit Python SDK maturity); overrides the personal TS-strict default for this team project

## Context

- **Event:** Moss-hosted Conversational AI Hackathon, YC SF. Build day is now; **submissions due 11 AM Sunday.** Track: Co-Pilot.
- **Team:** 3 people. Work must decompose into ~3 parallel ownable workstreams ("3 PRDs of one product") so all three can build simultaneously. The `handleTurn` contract is the integration seam that lets Voice and Live owners build against a mock while the Brain owner builds the real retrieval.
- **Why now:** real-time semantic retrieval (Moss) + voice cloning (Qwen) + multi-party voice rooms (LiveKit) just crossed the line of being possible together.
- **Sponsor stack:** Moss (core — live context retrieval) · LiveKit (core — live room/audio) · Qwen (voice clone) · Minimax (TTS fallback) · TrueFoundry (LLM gateway — optional/mention). Skip Unsiloed/AWS.
- **Architecture (locked):** Brain is I/O-agnostic so text→voice is a cheap swap, not a rewrite. Persona = cloned voice + system prompt. Namespace per user in Moss.
- **YC winning patterns (from research/):** working demo > pitch; new form factor not new model; one specific user; touch real data live. The moat = real-time, context-faithful retrieval.
- **Existing artifacts:** `research/01-what-wins-cheatsheet.md`, `research/02-yc-hackathon-winners.md`, `research/03-problem-landscape.md`; `tools/huggingface-skills/` (papers skill installed). `DEMO-PLAN.md` reflects an **earlier, stale framing** (manager's clone joins a meeting you're double-booked for, asks YOUR question; TypeScript) — to be reconciled to this standup-proxy framing or superseded.
- **Brainstorming, idea selection, and the discovery interview are DONE — not to be reopened.** This is build day: minimize analysis, maximize building.

## Constraints

- **Tech stack**: Python + LiveKit (Python SDK) — most mature for agents; team leans it. Ground all Moss/LiveKit/Qwen/Minimax SDK calls in current docs (source-driven); do not hallucinate SDK APIs.
- **Timeline**: ~24h build; submissions due 11 AM Sunday. Every phase must stay demo-able.
- **Team**: 3 people working in parallel — roadmap must expose 3 clear ownable workstreams against a shared contract.
- **Demo surface**: LiveKit playground + a Slack summary channel. No custom UI.
- **Security**: No secrets in repo. No API keys committed.
- **Demo integrity**: Demo only what is real; pitch enterprise/full-org-brain as vision.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Stack = Python + LiveKit | Most mature LiveKit SDK for agents; team leans it; overrides personal TS-strict default for this team project | — Pending |
| Build bottom-up: SPINE → VOICE → LIVE | Retrieval is the moat and everything depends on it; voice/room are layers, not prerequisites; never start with LiveKit plumbing | — Pending |
| Brain is I/O-agnostic (`handleTurn` contract) | Makes text→voice a cheap swap and lets 3 people parallelize against one seam | — Pending |
| Make retrieval visible on screen | Judges must SEE the moat (context→answer), not only hear it | — Pending |
| Real cloned voices + pre-cached demo lines | Cloned voice is the wow; pre-cache exact lines as day-of safety net | — Pending |
| One scripted manager-clone → teammate-clone exchange | Honors the agent→agent appeal while cutting fragile autonomous chatter | — Pending |
| Go/no-go: ship Slack-summary-only if spine doesn't land | Protects against the live-voice time sink; guarantees a demo-able fallback | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-06 after initialization*
