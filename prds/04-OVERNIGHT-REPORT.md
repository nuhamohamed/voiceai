# PRD-04 — Overnight Build Report

**Branch:** `feat/tony-live-agent` (committed locally, **NOT pushed** — review then push). **Generated:** overnight 2026-06-07.

## TL;DR

The live agent is **built and green on every automated check**. It joins a LiveKit room, answers the two scripted standup questions in the **cached cloned voice** while **live `retrieve()` drives the on-screen 🔎 Moss trace**, on the real merged stack (Nuha's real Moss + "Nuha" persona + 17-record corpus).

**One thing will undermine the demo until a teammate fixes it (not my lane):** Moss currently mis-ranks the Q2 "what's actually blocking it?" retrieval — see [🔴 Blocker](#-1-blocker-q2-retrieval-ranking-cross-lane). Everything I own is done; the trace plumbing is correct and will show the right chunks the moment retrieval ranking is fixed.

## ✅ Verified green (final audit, run twice, identical)

| Check | Result |
|---|---|
| `cd agent-py && uv run pytest -q` | **12 passed** (grounding + integration + agent evals) |
| `cd agent-py && uv run ruff check src/ tests/` | clean |
| agent import smoke | `IMPORT OK` |
| `pnpm --dir frontend lint` | passes (warnings only, vendored components) |
| `pnpm --dir frontend build` | ✓ Compiled successfully (Next 15.5.18 on node 25) |
| live Moss retrieval (status+blocking query) | returns ENG-412 chunk citing "refresh-token rotation… ENG-419" |
| agent wiring | `retrieve()` wired; 0 memory tools; 0 `moss` import; `StopResponse` + `preemptive_generation=False` |

## What was built (my lane)

- `agent-py/` — forked from `moss-hacker-starter`, adapted:
  - `src/agent.py` — `search_knowledge` → our `retrieve(query,"person_a")`; persona/instructions from `get_persona` (Nuha); `_publish_moss_context` emits the exact `moss_context` shape the frontend parses; memory tools + the starter's own MossClient removed; `preemptive_generation=False`; **`on_user_turn_completed`** routes the two scripted questions to cached cloned-voice WAVs (Q1 status→`update.wav`, Q2 blocker→`blocker.wav`) with `StopResponse`; short text greeting on join.
  - `src/grounding.py` — pure adapters (chunks → LLM text; chunks → `moss_context` payload).
  - `src/playback.py` — `wav_frames()` (derives `samples_per_channel` from bytes read — handles the bogus WAV header).
  - `tests/test_integration.py` — behavioral test: payload-shape units + WAV-decode for all 3 clips + a **live Moss** retrieval assertion (ran for real, passed).
- `frontend/` — trace panel rebranded ("🔎 Moss source"); renders `metadata.ref`/`source` badge + text + score; TS strict intact; builds clean.
- Commits: `9c56fd2` (rewire), `1f6a2e8` (update playback), `73a0d4b` (frontend), `ad76d85` (cached answers + integration test) + overnight docs.

## 🔴 #1 BLOCKER — Q2 retrieval ranking (cross-lane: `brain/` + `data/`)

For the demo-script's Q2 *"what's actually blocking it?"*, real Moss returns **ENG-418 / ENG-423 / MEL-9** — ENG-418 literally says *"does not block prod rollout."* The script's expected top-3 (`lin-eng-419`, `lin-eng-412-c-ivan-rotation`, `slack-security-ivan-rotation`) do **not** lead, for either the bare or a context-rich phrasing (MEL-9 ranks #1). **So the on-screen trace shows the wrong chunks at the moat moment.**

This is **not** in my lane (the agent + trace plumbing are correct — verified). Suggested fixes for Nuha/Melody:
- **`brain/retrieval.py`**: tune `QueryOptions(top_k=3, alpha=0.7)` — try higher `top_k` (5) and/or adjust `alpha`; consider a re-rank.
- **`data/person_a_corpus.jsonl`**: `MEL-9` ≈ `ENG-423` (near-duplicate "Backfill OAuth user IDs") dilute ranking and crowd the top-3; consider deduping or sharpening the rotation records' text.
- Re-verify with: `uv run --project agent-py python scripts/harness.py "what's actually blocking it?"` → the top chunks should be the ENG-419 / Ivan-rotation ones.

## 🎙️ Needs YOUR live verification (can't be done without a mic/browser)

1. **Run the demo:** from repo root, `pnpm dev` → open http://localhost:3000 → **Start call**, allow mic.
   - Ask **"What's the status of the auth migration?"** → clone should speak `update.wav` (cloned voice) + panel fills.
   - Ask **"What's actually blocking it?"** → clone should speak `blocker.wav` + panel fills (chunks currently mis-ranked — see blocker above).
2. **Confirm the `say(audio=…)` + `StopResponse` runtime behavior** — that the cached WAV actually plays, the LLM reply is suppressed (no double-answer), and the ~26–32s awaited `say()` doesn't stall the pipeline. (Signatures verified against LiveKit docs; runtime is the one thing untested.)
3. If retrieval ranking isn't fixed in time, the demo-script's documented fallback (text-on-screen trace, or Slack-summary-only) still lands the specificity.

## Prereqs already satisfied
- Moss `person_a` index built (`uv run --project agent-py python -m brain.ingest`, 17 docs). Re-run if the corpus changes.
- LiveKit creds in `agent-py/.env.local`; Moss keys in root `.env`. Frontend deps installed; build cached.

## Notes / trivia for the morning
- Frontend page title still reads "Person A — Standup Clone"; persona display name is "Nuha". One-line tweak in `frontend/app-config.ts` if you want the title to say Nuha (left as-is to preserve the verified-green snapshot).
- **Slack summary (LIV-04)** intentionally deferred (your call) — `slack_summary.wav` text + webhook is a ~10-line add when you want it.
- **Not pushed.** Suggested: review the diff, then `git push -u origin feat/tony-live-agent` and open the PR.
