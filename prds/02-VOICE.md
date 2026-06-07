# PRD 02 — Voice: Cloned Speech I/O

**Owner:** B · **Roadmap:** Phase 3 · **Requirements:** VOX-01..04
**Depends on:** Foundation contract only (parallel with Brain & Live; use the **stub** brain until Brain ships)

## Mission

Give the clone a voice — clone an absent teammate's voice, and wire **STT in / TTS out** around `handle_turn` so a spoken question becomes a spoken answer **in that person's cloned voice**. The cloned voice is the *wow*; the pre-cached demo lines are the safety net that guarantees it lands on stage.

## What you're building

```
spoken question ──STT──▶ text ──▶ handle_turn(text, persona_id) ──▶ response_text ──TTS(voice_id)──▶ spoken answer
                                  (import from brain.stub until Brain lands; then brain.contract)
```

## Scope

**In:**
- **VOX-01** Clone an absent teammate's voice (Qwen; **Minimax TTS as fallback**) → a usable `voice_id` per persona.
- **VOX-02** STT: spoken question → text suitable for `handle_turn`.
- **VOX-03** TTS: speak `handle_turn`'s `response_text` in the persona's cloned `voice_id`.
- **VOX-04** **Pre-cache the exact demo lines** as audio; play on demand if live cloning/TTS fails. *This is the day-of insurance — do it early, not last.*

**Out:** retrieval/LLM (you call `handle_turn`, you don't implement it), the LiveKit room transport (PRD 03 — though coordinate on audio format), the contract signature.

## Success criteria (what must be TRUE)

1. An absent teammate's voice is cloned (Qwen; Minimax fallback).
2. A spoken question is transcribed to text suitable for `handle_turn`.
3. `handle_turn`'s response is spoken back in the persona's cloned voice.
4. The exact demo lines are pre-cached as audio and play on demand if live TTS fails.

## Suggested slices (you plan the details)

- `03-01` Voice cloning + TTS in persona voice; **pre-cache demo lines** (build the safety net first).
- `03-02` STT for incoming questions, wired around `handle_turn`.

## Design decisions that are YOURS

- Streaming vs. batch TTS (latency vs. simplicity for the demo).
- STT engine choice + how you chunk/endpoint speech into a question.
- The fallback trigger: how you detect "live TTS failed" and switch to the cached clip cleanly (no awkward pause on stage).
- Audio format/handoff so Live (PRD 03) can pipe your output into the LiveKit room — **coordinate this with Owner C early.**

## SDKs you touch

**Qwen** (voice clone) · **Minimax** (TTS fallback) · an STT engine. **Ground every call in current docs** (`source-driven-development`); voice SDKs change fast — don't hallucinate API shapes.

## Integration points

- **Upstream:** `handle_turn` from `brain.stub` now → `brain.contract` once Brain (PRD 01) lands. No code change beyond the import.
- **Downstream:** Live (PRD 03) consumes your STT (room audio → text) and your TTS (response_text → room audio). Agree the function boundary with Owner C so it slots into the LiveKit agent loop.

## Next

`/gsd-plan-phase 3` for a detailed task plan, or build from the slices. **Restart Claude Code first.**
