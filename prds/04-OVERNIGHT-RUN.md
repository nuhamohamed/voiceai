# PRD-04 — Overnight Autonomous Build Charter

**Owner:** Tony (Claude, autonomous) · **Branch:** `feat/tony-live-agent` · **Started:** 2026-06-07 (overnight)

Tony is asleep. This file is the standing goal + state for an autonomous build-test-validate
loop. Each cycle reads this file, advances, validates, and appends to the Iteration Log.

## Goal

Finish the PRD-04 live agent and validate the full integration with the other lanes' outputs
(Melody's corpus, Nuha's `retrieve()`/voice config + cached WAVs), to the maximum extent that is
verifiable WITHOUT a human at the microphone/browser.

## Done condition (all must hold, stable across 2 consecutive cycles)

1. `uv --directory agent-py run pytest -q` — green
2. `uv --directory agent-py run ruff check src/` — clean
3. agent import-smoke: `cd agent-py && uv run python -c "import sys; sys.path.insert(0,'src'); import agent; print('OK')"`
4. `pnpm --dir frontend lint` and `pnpm --dir frontend build` — succeed
5. **Behavioral integration test** (`agent-py/tests/test_integration.py`, written by the loop) passes:
   - feeds the demo question as TEXT through the agent's retrieval path
   - asserts `retrieve("...", "person_a")` surfaces ENG-419 (refresh-token rotation) as a top chunk
   - asserts the grounded answer text contains the key specifics (ENG-419 / Ivan / rotation)
   - asserts the `moss_context` payload validates against the frontend contract
     (`type:"moss_context"`, `data.matches=[{text, score, metadata:{ref,source}}]`)
   - asserts each `audio/demo/*.wav` decodes to a valid `rtc.AudioFrame` (bogus-header-safe)
6. Final integration audit (workflow agent) reports `pass` with no major/blocking issues.

## Out of scope for autonomy (human verifies on waking — NOT blocking "done")

- The literal live voice demo: `pnpm dev` → browser → mic → speak the follow-up → hear the
  clone + watch the panel. (No human at the mic/browser overnight.)
- Task 6 clone-voice answer LIVE behavior (`say(audio=)`+`StopResponse` interplay). The loop may
  implement the CODE + static/unit checks, but marks live behavior as "requires human verification."

## Safety rails

- **NEVER push, NEVER open a PR.** All work stays local on `feat/tony-live-agent`.
- **Lane discipline:** only edit `agent-py/`, `frontend/`, new test files, and `prds/`. Do NOT edit
  `brain/retrieval.py`, `personas.py`, `voice/*`, `data/*`. `git pull origin main` (read) each cycle
  to integrate teammates; the agent calls `retrieve()` so stub→real Moss is transparent.
- **Bounded:** max 10 cycles. **Stuck-detection:** if the same failure persists across 3 cycles,
  STOP and write a detailed blocker report instead of looping.
- Commit each green increment locally. Append to the Iteration Log every cycle.
- No secrets in commits (`.env`/`.env.local` are gitignored).

## Loop mechanism

Primary driver: each background build/validate **workflow** re-invokes the controller on completion.
Safety net: a long `ScheduleWakeup` heartbeat. On each wake the controller: (1) `git pull origin main`,
(2) checks if a build workflow is still running — if so, reschedules and yields, (3) else runs the
validation suite / reads the last audit, (4) if done → final report + stop, (5) else if cycles remain
and not stuck → launch the next build/fix/validate workflow + reschedule, (6) else → blocker report + stop.

## Cycle plan (adapt as state dictates)

- **Cycle 1** (workflow `wf_ee6a351d-219`): build Tasks 0–4 + static integration audit.
- **Cycle 2:** fix audit findings; write `tests/test_integration.py` (the behavioral test); run full suite.
- **Cycle 3:** implement Task 6a code + unit test (routing/WAV); pull main; full suite.
- **Cycle 4+:** harden — adversarial integration bug-hunt, re-run suite, pull main, until stable green ×2.
- **Final:** write `prds/04-OVERNIGHT-REPORT.md` (what works, what needs human live-check, exact run commands).

## Iteration Log

- **Cycle 1 — launched** `wf_ee6a351d-219` (Tasks 0–4 build + per-task adversarial review + audit). Awaiting completion.
