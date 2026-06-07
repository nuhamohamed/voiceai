# 04 — Demo-Readiness Report (Standup Proxy, Person A = Nuha)

**Verdict:** The backend/agent scripted demo path is **READY**, conditional on (a) the live mic/browser check and (b) the in-flight UI — and on applying the one-line interruption guard below before going on stage. The spoken moat is safe (cached WAVs via keyword routing + StopResponse); the on-screen retrieval *trace* has a HIGH-severity issue that lives in the data + frontend lanes, not the backend code path.

Synthesized from four validation passes: SUITE_HEALTH, RETRIEVAL_ROBUSTNESS, DEMO_RISK, BEHAVIORAL_TEST. The lone `pass=false` (DEMO_RISK) does not flip the verdict: every one of its blocking items lands in a bucket this verdict already excludes (live-mic timing, corpus data lane, frontend trace rendering) — none is a pure backend-scripted-path defect.

---

## Verified green

| Check | Result | Source |
|---|---|---|
| Test suite (agent-py) | `12 passed` (19 with the new uncommitted behavioral tests) | SUITE_HEALTH, BEHAVIORAL_TEST |
| `ruff check` / `ruff format` | `All checks passed!` / clean | SUITE_HEALTH, BEHAVIORAL_TEST |
| Import smoke | `IMPORT OK` | SUITE_HEALTH |
| **Q1 status** — routing | status+auth/migration → `update.wav` + StopResponse, `retrieve()` called | BEHAVIORAL_TEST (drives real `on_user_turn_completed`) |
| **Q1 status** — required context in top-6 | ENG-412 + Nuha status comment + #infra Slack update all present | SUITE_HEALTH |
| **Q2 blocker (moat)** — routing | "block" → `blocker.wav` + StopResponse, `retrieve()` called | BEHAVIORAL_TEST |
| **Q2 blocker (moat)** — required context in top-6 | ENG-419 (0.902) + refresh-token rotation + Ivan's Jun-3 review all present | SUITE_HEALTH, BEHAVIORAL_TEST (bare Q2 string, live Moss, PASS not skipped) |
| Off-script fall-through | "how are you feeling today?" → no StopResponse, no WAV, clean LLM path | BEHAVIORAL_TEST |
| Spoken-transcript ↔ WAV lock | say() text contains `PR #847` / `ENG-419` (Q1), `ENG-419` / `reuse detection` (Q2) — matches demo-script | BEHAVIORAL_TEST |
| Frontend payload shape | `{type:'moss_context', data:{query, matches:[{text,score,metadata:{ref,source}}], timestamp}}` matches contract | BEHAVIORAL_TEST |
| WAV decode | `update.wav` 31.8s, `blocker.wav` 25.8s, mono 24kHz 16-bit; decode robust to bogus data-chunk header | DEMO_RISK, BEHAVIORAL_TEST |
| Persona name | `personas.PERSONAS['person_a'].name == "Nuha"` (verified `personas.py:29`) | this report |
| `preemptive_generation=False` | prevents speculative generic-voice leak before cached WAV fires | DEMO_RISK |

**Bottom line on the moat:** the *spoken* Q2 answer is correct and cached — it names ENG-419, refresh-token rotation, reuse detection. The *on-screen trace* is the exposed surface (see HIGH risk #2).

---

## Retrieval robustness (live Moss, person_a, top_k=6, alpha=0.7)

The LLM path grounds on all 6 returned chunks, so "is the answer-bearing chunk in the top-6 set" is the bar that matters for off-script judge questions.

**Strong (answer-bearing chunk near the top):**
- "what's the security concern?" — Cal Security Review + Ivan #security (strong)
- "what shipped this week?" — #infra status, callback shipped Tuesday, PR #847 (strong)
- "what did Ivan flag?" — ENG-419 rotation at #1, Ivan's requirement well-covered
- "what are you working on?" — ENG-412 Auth migration (Owner: Nuha, In Progress) at #1
- "who is working on the frontend?" / "what's the status of PKCE?" — PKCE + "Owner: Jamie" surfaced

**Works but weak-at-#1 (correct context present lower in the set; #1 is an off-topic Backlog/stretch ticket):**
- "is the migration done?" — #1 ENG-455 (Backlog), real status at #2/#4/#6
- "when does it ship to prod?" — Jun-9 date in #infra chunks (#4/#5), not #1
- "what's left before launch?" — Ivan "one required change" at #1, ENG-419 blocker only #7

**Tally:** 10/10 off-script judge questions surface answer-bearing context within top-6 (3 are weak-at-#1). Both scripted demo questions are safe regardless of ranking because they bypass live ranking via cached WAVs.

**Root cause of every weak/inverted ranking:** `data/person_a_corpus.jsonl` carries duplicate parallel ticket sets — hand-authored `ENG-*` and Linear-pulled `MEL-*` mirrors of the same tickets. The mirrors crowd the top-k and push answer-bearing chunks down. (Named in `brain/retrieval.py`'s own `top_k=6` comment.)

---

## Risks before the live demo (ranked by severity, deduped across all four reports)

### HIGH — 1. 26–32s cached answers are interruptible
The two `session.say(...)` calls (`agent-py/src/agent.py` L98, L118) pass **no** `allow_interruptions=False`; `say()` defaults to interruptible. On stage, the PM starting Q2 early, cross-talk, or a VAD false-positive will cut the clone's scripted answer off mid-sentence (and truncate history to what was heard).
- **Mitigation (do BEFORE stage):** pass `allow_interruptions=False` to both `say()` calls (LiveKit "Uninterruptable Agent" recipe). One-line fix. Plus rehearse the PM holding silence until each ~30s clip finishes.
- **Lane:** agent.py owner (Tony). *Left unfixed here by design — this report is synthesis; BEHAVIORAL_TEST deliberately did not edit agent.py.*

### HIGH — 2. Q2 on-screen Moss trace contradicts the spoken moat
For the exact PM phrasing "what's actually blocking it?", live Moss ranks: **#1 ENG-418 (0.982) — text reads verbatim "does not block prod rollout on its own"**; #2 ENG-423 (backfill, reverse "blocked-by" direction); **#3 ENG-419 (0.902) — the real blocker.** The scripted branch publishes this raw top-6 to the on-screen panel *before* speaking the (correct, cached) WAV — so a judge reading the trace top-down sees the #1 line say the opposite of the voice, at the exact moat moment. Verified **not** fixable by rephrasing (4 Q2 variants tested; none ranks ENG-419/MEL-8 at #1) — it is corpus-bound.
- **Mitigation:** (a) corpus lane — dedupe `ENG-*`/`MEL-*` mirrors so ENG-419 outranks ENG-418 (per `brain/retrieval.py`'s comment, also lets top_k drop back toward 3); and/or (b) frontend lane — pin/highlight the grounded chunk (agent already computes `grounds on: chunks[0]`) or filter the published payload to refs the cached answer cites (ENG-419 / Ivan rotation / #security) instead of rendering raw score order.
- **Lane:** Melody/Nuha (data dedupe) + frontend agent (trace rendering). *Both forbidden to this lane; recommendation only.*

### MEDIUM — 3. Stale "Tony Nguyen" docs live in the Moss person_a index
Queries surface `#infra … Tony Nguyen`, `ENG-412 comment — Tony`, and a Cal-event variant naming Tony. `grep -c 'Tony Nguyen' data/person_a_corpus.jsonl = 0` — these are leftover from a prior ingest (~20 docs in the index vs 17 in the file). They rank top-6 for "what shipped this week?" and "what's the security concern?" and would render a non-Nuha author name in the on-screen trace, breaking the persona illusion.
- **Mitigation:** Nuha — clear and rebuild the person_a index from the current 17-record corpus (re-run `brain/ingest.py`); verify via `scripts/harness.py` that no "Tony Nguyen" refs appear.
- **Lane:** Nuha (index). *Ingest mutates shared Moss state — out of this lane.*

### MEDIUM — 4. Q1 status trace leads with off-topic Backlog tickets
"what's the status of the auth migration?" top-6: #1 MEL-9 Backfill (Todo), #2 ENG-455 (Backlog stretch), #3 MEL-10 (Backlog), #4 ENG-412, #5 MEL-5 (real status comment), #6 #infra. Less damaging than #2 (nothing contradicts the spoken answer) but the demo opener's trace looks noisy. Same duplicate-corpus root cause as #2.
- **Mitigation:** same as #2 — corpus dedupe, or pin/highlight the grounded chunk.
- **Lane:** Melody/Nuha (data) + frontend.

### MEDIUM — 5. Keyword routing mis-fires on near-miss phrasings
Any utterance containing "block" routes to `blocker.wav` regardless of topic ("any blockers on your other projects?", "is anything blocking the PKCE work?"). Natural status openers that lack the topic word fall through to the **generic** LLM voice ("how is the migration going?", "what's the status of PKCE?", "what's your status today?" — status branch requires status-word AND auth/migration).
- **Mitigation:** coach the PM to use the exact scripted phrasings (which route correctly). Longer term: require auth/migration context on the blocker branch and broaden the status-word set, or gate routing on a demo flag.
- **Lane:** agent.py owner (Tony) / PM coaching.

### MEDIUM — 6. Off-script questions answer in a generic voice
Only the two cached WAVs are in Nuha's cloned voice; everything else goes through the live LLM + `inference.TTS` (generic voice id, `agent.py` L174). A judge follow-up right after the two cloned answers is an audible voice mismatch.
- **Mitigation:** set expectation that only the two demo questions are pre-rendered in the clone voice; steer judges to the scripted follow-up; optionally pre-render a couple of likely follow-ups as extra cached WAVs.
- **Lane:** Tony (routing) + Nuha (voice clone).

### MEDIUM — 7. On-screen participant name not set by the agent
`personas.name == "Nuha"` is correct, but `agent-py/src/` has **no** `set_name`/identity wiring (only `publish_data`); the registered dispatch name is `agent-py`. Whether the room shows "Nuha" depends entirely on the frontend. (Note: `docs/demo-script.md:115` saying the name is "Person A" is **stale** — it's already "Nuha".)
- **Mitigation:** verify the live room renders the participant as "Nuha", not "agent-py". If the frontend doesn't override it, wire the display name from `personas.name`.
- **Lane:** frontend agent (coordinate). *Out of this lane to inspect frontend.*

### LOW — 8. Weak-at-#1 off-script questions could mislead an over-weighting LLM
"is it done?", "when does it ship?", "what's left?" put a Backlog/stretch ticket at #1; if the LLM over-weights chunk #1 it could understate progress or miss the Jun-9 date. The agent instruction already bounds this ("ground only in returned context; say 'not sure' if uncovered").
- **Mitigation:** corpus dedupe lifts answer-bearing chunks; optionally lower top_k toward 3 *after* dedupe.
- **Lane:** Nuha (corpus).

---

## What still needs a human (live mic / browser — not covered by automated tests)

The behavioral suite proves routing, retrieval, payload shape, and WAV decode mic-free (room=None). These still require a live room rehearsal:

1. **STT → keyword feed** — that the real transcript actually feeds the keyword match.
2. **Turn detection** — that `on_user_turn_completed` fires at the right moment.
3. **Real audio playback** — `session.say(audio=wav_frames(...))` plays the ~26–32s WAV cleanly into the room.
4. **Data-channel publish** — the `moss_context` message reaches the frontend panel (the `publish_data` path is no-op'd in tests because room=None).
5. **Interruption / timing rehearsal** — confirm the (newly guarded) clips play to completion; PM holds silence; room stays quiet. *(Depends on HIGH risk #1 fix landing first.)*
6. **On-screen label** — confirm the room shows "Nuha" (risk #7).
7. **On-screen trace sanity for Q2** — confirm the panel does not visibly contradict the spoken answer (risk #2); rehearse the demo-script go/no-go fallback (text-on-screen mode) as backup.
