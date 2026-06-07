# Roadmap: Standup Proxy (Clone Agent)

## Overview

A ~24h hackathon build for a *standup proxy* — when a teammate can't attend standup, their clone joins in their cloned voice and answers follow-up questions grounded in that person's real context (Slack/calendar/Linear) retrieved live from Moss. The journey is bottom-up and always demo-able: first a shared **Foundation** locks the `handleTurn` integration contract, then three parallel workstreams owned by the 3-person team — the **Brain** (context retrieval, the moat), the **Voice** (cloned speech I/O), and the **Live** room (LiveKit orchestration + Slack summary, where everything assembles into the 2-minute demo). Foundation is the only hard prerequisite: Brain, Voice, and Live each depend only on the contract, so all three can be built simultaneously (Voice and Live mocking the brain until real retrieval lands).

**Team ownership (3 PRDs):** Owner A → Phase 2 (Brain) · Owner B → Phase 3 (Voice) · Owner C → Phase 4 (Live + integration). All three unblock after Phase 1.

**Demo north star:** in a live standup, a follow-up question to an absent teammate's clone → it visibly retrieves from Moss and answers in that person's real voice with the actual specifics.

## Phases

- [ ] **Phase 1: Foundation & Contract** - Python+LiveKit scaffold, the `handleTurn` brain seam, personas, and a text harness
- [ ] **Phase 2: Brain — Context Retrieval (SPINE)** - Moss ingestion + retrieve→LLM grounded answers, with retrieval made visible (the moat + go/no-go gate)
- [ ] **Phase 3: Voice — Cloned Speech I/O** - Cloned voice, STT/TTS, and pre-cached demo lines
- [ ] **Phase 4: Live — Room, Orchestration & Summary** - LiveKit multi-party room, the manager→teammate clone exchange, and Slack summary; full demo assembly

## Phase Details

### Phase 1: Foundation & Contract
**Goal**: Stand up the Python+LiveKit project and lock the single integration seam (`handleTurn`) plus personas and a text harness, so all three workstreams can build in parallel against a stable contract.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: FND-01, FND-02, FND-03, FND-04
**Success Criteria** (what must be TRUE):
  1. The repo runs in Python with dependencies installed and secrets loaded from `.env` (no keys committed)
  2. `handleTurn(incoming_text) -> { response_text }` exists and is importable by both a text harness and (later) the voice loop
  3. 2 hardcoded personas (name + system prompt + voice id) load by namespace
  4. Running the text harness feeds a transcript line to `handleTurn` and prints a response (stubbed retrieval is fine at this point)
**Plans**: 3 plans

Plans:
- [ ] 01-01: Project scaffold + dependency/secret management (`.env` loader)
- [ ] 01-02: `handleTurn` contract + persona config loader (stubbed brain)
- [ ] 01-03: Text harness that pipes transcript → `handleTurn` → printed response

### Phase 2: Brain — Context Retrieval (SPINE)
**Goal**: Make the clone answer a follow-up with the right, real specifics retrieved from the speaker's Moss namespace — and make that retrieval visible. This is the moat and the go/no-go gate.
**Mode:** mvp
**Depends on**: Phase 1 (the `handleTurn` contract)
**Requirements**: BRN-01, BRN-02, BRN-03, BRN-04, FBK-01
**Success Criteria** (what must be TRUE):
  1. Each persona's context (Slack/cal/Linear export) is chunked and indexed in Moss under a per-user namespace
  2. `handleTurn` retrieves from the speaker's namespace and returns a factually grounded answer with the real specifics
  3. The retrieval is shown on screen (e.g. `🔎 Moss → [chunk used]`) next to the answer
  4. A scripted demo question about an absent teammate's work returns the correct specific answer in text (the killer moment, provable without voice)
  5. **Go/no-go:** if criteria 2–4 aren't landing after this phase, the Slack-summary-only fallback (FBK-01) is wired as the simpler demo
**Plans**: 3 plans

Plans:
- [ ] 02-01: Per-user ingestion → chunk → Moss namespace
- [ ] 02-02: Retrieve→LLM grounded `handleTurn` implementation + visible retrieval trace
- [ ] 02-03: Scripted demo-question validation + Slack-summary-only fallback wiring

### Phase 3: Voice — Cloned Speech I/O
**Goal**: Give the clone a voice — clone an absent teammate's voice and wire STT in / TTS out around `handleTurn`, with the exact demo lines pre-cached as a safety net. Built in parallel with Phase 2 against the contract (mock brain until real retrieval is ready).
**Mode:** mvp
**Depends on**: Phase 1 (the `handleTurn` contract) — parallel to Phase 2
**Requirements**: VOX-01, VOX-02, VOX-03, VOX-04
**Success Criteria** (what must be TRUE):
  1. An absent teammate's voice is cloned (Qwen; Minimax TTS fallback)
  2. A spoken question is transcribed to text suitable for `handleTurn`
  3. `handleTurn`'s response is spoken back in the persona's cloned voice
  4. The exact demo lines are pre-cached as audio and play on demand if live cloning/TTS fails
**Plans**: 2 plans

Plans:
- [ ] 03-01: Voice cloning + TTS in persona voice (with pre-cached demo lines)
- [ ] 03-02: STT for incoming questions, wired around the `handleTurn` contract

### Phase 4: Live — Room, Orchestration & Summary
**Goal**: Assemble the full demo — a LiveKit multi-party room where an absent teammate's clone joins, delivers its update, answers a scripted manager-clone follow-up in voice from Moss context, and posts action items to Slack on adjourn.
**Mode:** mvp
**Depends on**: Phase 1 (contract); integrates Phase 2 (Brain) + Phase 3 (Voice)
**Requirements**: LIV-01, LIV-02, LIV-03, LIV-04
**Success Criteria** (what must be TRUE):
  1. A multi-party voice room runs via LiveKit Agents with real-time turn-taking, demoable in the LiveKit playground
  2. An absent teammate's clone joins the standup and delivers its update in cloned voice
  3. One scripted manager-clone → teammate-clone exchange runs end-to-end: question → visible Moss retrieval → spoken grounded answer
  4. On adjourn, the standup is summarized and action items are posted to a Slack summary channel
**Plans**: 3 plans

Plans:
- [ ] 04-01: LiveKit Agents room + real-time turn-taking (playground-demoable)
- [ ] 04-02: Integrate Brain + Voice into the room; scripted manager→teammate exchange
- [ ] 04-03: Adjourn → summarize → post action items to Slack

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4. With a 3-person team, Phases 2, 3, and 4 can be worked in parallel by their owners once Phase 1 lands (each depends only on the contract).

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Contract | 0/3 | Not started | - |
| 2. Brain — Context Retrieval | 0/3 | Not started | - |
| 3. Voice — Cloned Speech I/O | 0/2 | Not started | - |
| 4. Live — Room, Orchestration & Summary | 0/3 | Not started | - |
