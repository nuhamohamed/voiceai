# PRD 03 — Live: Room, Orchestration & Summary

**Owner:** C · **Roadmap:** Phase 4 · **Requirements:** LIV-01..04
**Depends on:** Foundation contract; **integrates** Brain (PRD 01) + Voice (PRD 02). Use stubs/mocks for both until they land — scaffold the room first.

## Mission

Assemble the full demo. A **LiveKit multi-party voice room** where an absent teammate's clone joins, gives its update, **answers a scripted manager-clone follow-up in voice from Moss context**, and on adjourn posts action items to a **Slack summary channel**. You own the surface the judges actually see.

## What you're building

```
LiveKit room (playground)
  ├─ clone joins as a participant, speaks its update (TTS, PRD 02)
  ├─ manager-clone asks ONE scripted follow-up
  │     question ──STT──▶ handle_turn(text, persona_id) ──▶ response_text + retrieved
  │                         (Brain, PRD 01)        │
  │     retrieved ──▶ show on screen (🔎 Moss → chunk)   response_text ──TTS──▶ spoken answer
  └─ on adjourn ──▶ summarize transcript ──▶ post action items to Slack
```

## Scope

**In:**
- **LIV-01** Multi-party voice room via **LiveKit Agents** with real-time turn-taking, demoable in the **LiveKit playground**.
- **LIV-02** An absent teammate's clone joins and delivers its update in cloned voice.
- **LIV-03** **One scripted manager-clone → teammate-clone exchange**: question → visible Moss retrieval → spoken grounded answer. (One clean exchange — *not* autonomous chatter; that's vision, out of scope.)
- **LIV-04** On adjourn: summarize the standup → post action items to a **Slack summary channel**.

**Out:** the brain internals (call `handle_turn`), the voice models (call Voice's STT/TTS), autonomous multi-agent conversation, auth/OAuth, custom UI.

## Success criteria (what must be TRUE)

1. A multi-party voice room runs via LiveKit Agents with real-time turn-taking, demoable in the playground.
2. An absent teammate's clone joins and delivers its update in cloned voice.
3. The scripted manager→teammate exchange runs end-to-end: question → visible retrieval → spoken grounded answer.
4. On adjourn, the standup is summarized and action items posted to a Slack summary channel.

## Suggested slices (you plan the details)

- `04-01` LiveKit Agents room + real-time turn-taking (get *something* talking in the playground early).
- `04-02` Integrate Brain (`handle_turn`) + Voice (STT/TTS) into the room; wire the scripted manager→teammate exchange + the on-screen retrieval overlay.
- `04-03` Adjourn → summarize → post action items to Slack.

## Design decisions that are YOURS

- Turn-taking / who-speaks-when orchestration for the scripted exchange.
- How the on-screen retrieval trace is surfaced in the playground (this is the *visible moat* — make sure judges see context→answer, not just hear it).
- Summary format + which Slack channel/webhook; what counts as an "action item."
- Start against **mock** `handle_turn` (stub) and **canned** audio (Voice's pre-cached lines) so you're never blocked.

## SDKs you touch

**LiveKit Agents (Python SDK)** — rooms, participants, turn-taking · **Slack** (incoming webhook or bot token) for the summary post. **Ground every LiveKit call in current docs** — use the **`livekit-docs` MCP** and `source-driven-development`; the Agents SDK moves fast, do not hallucinate APIs.

## Integration points

- **Brain (PRD 01):** `handle_turn(text, persona_id) -> TurnResult` — import `brain.stub` now, swap to `brain.contract` when ready.
- **Voice (PRD 02):** STT (room audio → text) and TTS (`response_text` → room audio). **Agree the audio boundary with Owner B early** — it's the trickiest seam in the assembly.

## Next

`/gsd-plan-phase 4` for a detailed task plan, or build from the slices. **Restart Claude Code first.**
