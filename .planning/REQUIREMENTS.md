# Requirements: Standup Proxy (Clone Agent)

**Defined:** 2026-06-06
**Core Value:** The clone answers a live follow-up question with the right, real specifics retrieved from that person's context in Moss — visibly and in their cloned voice.

## v1 Requirements

Requirements for the hackathon demo. Each maps to a roadmap phase. Categories are organized around a shared **Foundation** plus three parallel workstreams (**Brain**, **Voice**, **Live**) so a 3-person team can own one each.

### Foundation (shared seam — built first, together)

- [ ] **FND-01**: Python + LiveKit project scaffolded with dependency management and a `.env`-based secret loader (no keys in repo)
- [ ] **FND-02**: `handleTurn(incoming_text) -> { response_text }` brain interface defined as the single integration contract, callable from both a text harness and the voice loop
- [ ] **FND-03**: 2 hardcoded personas defined as config (name + system prompt + voice id), loadable by namespace
- [ ] **FND-04**: A text harness that feeds transcript text to `handleTurn` and prints the response, so the brain is iterable without any voice/room plumbing

### Brain — Context Retrieval (the SPINE / moat)

- [ ] **BRN-01**: Per-user context (Slack / calendar / Linear export) is chunked and indexed into Moss under a per-user namespace
- [ ] **BRN-02**: `handleTurn` retrieves relevant chunks from the speaker's Moss namespace, then calls the LLM to produce a grounded answer with the real specifics
- [ ] **BRN-03**: Retrieval is rendered visibly (e.g. `🔎 Moss → [chunk used]`) alongside the answer so the context→answer link is observable
- [ ] **BRN-04**: A scripted demo question about an absent teammate's work returns a factually specific answer drawn from that teammate's indexed context (the killer moment, provable in text)

### Voice — Cloned Speech I/O

- [ ] **VOX-01**: An absent teammate's voice is cloned (Qwen; Minimax TTS fallback) and the clone's responses are spoken in that voice
- [ ] **VOX-02**: Speech-to-text converts an incoming spoken question into text for `handleTurn`
- [ ] **VOX-03**: Text-to-speech speaks `handleTurn`'s response in the persona's cloned voice
- [ ] **VOX-04**: The exact demo lines are pre-cached as audio as a day-of safety net if live cloning/TTS fails

### Live — Room, Orchestration & Summary

- [ ] **LIV-01**: A multi-party voice room runs via LiveKit Agents with real-time turn-taking, demoable in the LiveKit playground
- [ ] **LIV-02**: An absent teammate's clone joins the standup and delivers their update in their cloned voice
- [ ] **LIV-03**: One scripted manager-clone → teammate-clone exchange occurs — the manager's clone asks a follow-up and the teammate's clone answers from Moss context, in voice
- [ ] **LIV-04**: On adjourn, the standup is summarized and action items are posted to a Slack summary channel

### Fallback (go/no-go contingency)

- [ ] **FBK-01**: If the spine (right answer from real context) isn't landing after the first build block, a Slack-summary-only path delivers the same idea without live voice

## v2 Requirements

Acknowledged but deferred — not in the hackathon roadmap.

### Vision

- **VIS-01**: Full company brain — org-wide context composition across all employees
- **VIS-02**: Slack OAuth + multi-tenant ingestion (replace hardcoded personas)
- **VIS-03**: Autonomous multi-agent standup (clones freely converse, not one scripted exchange)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full company brain / org-wide context | Vision only; the hard wedge, pitched not built today |
| Slack OAuth / multi-tenant auth | Hackathon uses hardcoded personas; auth is post-hackathon |
| Autonomous agent-to-agent chatter | Team cut it; demo ONE scripted manager→teammate exchange, pitch rest as vision |
| Screen / OS watching | Not core to standup-proxy value; time sink |
| Custom UI / web frontend | Demo runs in LiveKit playground + Slack channel |
| TypeScript stack | Team builds in Python (LiveKit SDK maturity); supersedes TS-strict default |

## Traceability

Which phases cover which requirements. Populated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FND-01 | Phase 1 | Pending |
| FND-02 | Phase 1 | Pending |
| FND-03 | Phase 1 | Pending |
| FND-04 | Phase 1 | Pending |
| BRN-01 | Phase 2 | Pending |
| BRN-02 | Phase 2 | Pending |
| BRN-03 | Phase 2 | Pending |
| BRN-04 | Phase 2 | Pending |
| FBK-01 | Phase 2 | Pending |
| VOX-01 | Phase 3 | Pending |
| VOX-02 | Phase 3 | Pending |
| VOX-03 | Phase 3 | Pending |
| VOX-04 | Phase 3 | Pending |
| LIV-01 | Phase 4 | Pending |
| LIV-02 | Phase 4 | Pending |
| LIV-03 | Phase 4 | Pending |
| LIV-04 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-06*
*Last updated: 2026-06-06 after initial definition*
