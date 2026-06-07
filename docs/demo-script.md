# Demo Script — Standup Proxy (Person A = Tony Nguyen)

The 2-minute live demo. Two questions to the absent teammate's clone; the
second one is where the moat lands.

## Setup (one paragraph for the judges)

> "Tony can't make our standup today. Normally that means we lose 10 minutes
> guessing where his work stands. Instead — his AI clone is here. It's joined
> the call as a participant, it has his real context from Linear and Slack
> indexed in Moss, and it'll answer questions in his cloned voice. Watch the
> screen — every chunk it retrieves shows up live."

## Cast

- **Tony Nguyen** — absent teammate. Backend engineer. The clone speaks as him.
- **Ivan Chubs** — Security. Flagged the blocker.
- **Jamie** — Frontend engineer working on PKCE in parallel.
- **PM (live in the room)** — asks the two demo questions.

## Q1 — Status question (opening)

**PM (spoken):**
> "Tony — what's the status of the auth migration?"

**Expected on-screen retrieval (🔎 Moss trace):**
1. `lin-eng-412` — ENG-412 / MEL-5 Auth migration ticket body
2. `lin-eng-412-c-tony-status` — Tony's Jun 5 status comment
3. `slack-infra-tony-update` — Tony's #infra Jun 5 status post

**Expected synthesized answer (spoken in Tony's cloned voice):**
> "The backend OAuth callback and token exchange shipped Tuesday — PR #847
> merged and deployed to staging Wednesday, sign-in works there. Ivan reviewed
> the spec Wednesday and flagged that we need sliding-window refresh-token
> rotation with reuse detection before prod. I'm implementing that now under
> ENG-419 — should land Friday. Jamie's doing PKCE on the frontend in parallel
> under ENG-418. Earliest prod rollout: Tuesday next week."

## Q2 — Follow-up (the moat moment)

**PM (spoken):**
> "What's actually blocking it?"

**Expected on-screen retrieval (🔎 Moss trace):**
1. `lin-eng-412-c-ivan-rotation` — Ivan's rotation proposal comment
2. `lin-eng-419` — the refresh-token rotation ticket
3. `slack-security-ivan-rotation` — Ivan's #security Jun 3 message

**Expected synthesized answer (spoken in Tony's cloned voice):**
> "Ivan's concern is that the current implementation issues long-lived refresh
> tokens — if one leaks, the attacker has a long window. He wants each refresh
> to rotate the token and revoke the old one, with reuse detection that
> invalidates the whole token family if a stale refresh gets replayed. It's a
> bigger lift than I'd scoped, so I added it as ENG-419 and started Thursday.
> Should be done Friday for Ivan's review."

## Adjourn — Slack summary

When the standup ends, Tony's clone posts to the Slack summary channel:

> **Tony's standup proxy summary** — auth migration: backend shipped to
> staging Tuesday; blocked on refresh-token rotation (ENG-419) for prod;
> targeting Tue Jun 9 rollout. Action: Tony to finish ENG-419 for Ivan's
> review by Fri EOD. Frontend PKCE (ENG-418, Jamie) in parallel.

## Go/no-go fallback

If `retrieve()` doesn't surface the right chunks on Q2 in rehearsal:

1. **First fallback:** swap to text-on-screen mode — the moat (retrieval +
   specific answer) still shows visually even if the voice loop has issues.
2. **Last resort:** ship Slack-summary-only — clone doesn't join the room,
   instead a digest is posted to the Slack channel ahead of the meeting.

## Why this lands

- **Specificity sells.** "Ivan flagged sliding-window refresh-token rotation
  with reuse detection" is the kind of detail you can't fake with a generic
  LLM — it has to come from real retrieved context.
- **Visible retrieval = the moat shown, not just heard.** Judges see the
  chunks light up before the voice answers.
- **Two questions, ~30s each.** Tight enough to demo cleanly, dense enough
  to feel like a real teammate caught up on his work.

## Corpus that grounds this

All 11 records live in `data/person_a_corpus.jsonl` (PR #3). Nuha loads this
file into Moss under `index_name="person_a"` (matches
`personas.PERSONAS["person_a"].moss_index`). If real Linear-pulled records
have been appended (via `scripts/pull_linear.py`), they coexist with the
hand-authored ones — retrieval picks the best semantic match at query time.
