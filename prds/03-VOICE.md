# PRD 03 — Voice: Cloned Speech (Qwen / Minimax)

**Owner:** Nuha · **Roadmap:** Phase 3 · **Requirements:** VOX-01..04
**Works alone.** **Hands off:** the voice config → Tony.

## Mission

Make the clone **sound like Person A**. Clone A's voice, provide the speak-in-A's-voice config the agent uses, the speech-to-text piece, and **pre-cached demo lines** as a stage safety net. Independent of Moss and the room — you can do this anytime.

## What you build

1. **VOX-01** Clone Person A's voice in **Qwen** (Minimax as TTS fallback) → a usable `voice_id`.
2. **VOX-03** A TTS config that, given text, **speaks it in A's cloned voice** — packaged so Tony can plug it into LiveKit's TTS slot.
3. **VOX-02** STT choice (e.g. the Deepgram plugin from the Moss×LiveKit install) so a spoken question becomes text.
4. **VOX-04** **Pre-cache the exact demo lines** as audio files; a way to play them if live TTS glitches on stage. *Do this early — it's the insurance.*

## Scope

**In:** voice cloning, TTS config, STT choice, cached lines. **Out:** retrieval (your PRD `02`), the room/turn-taking/assembly (Tony — he wires your config in). You produce a **voice config + audio**, not the agent.

## Success criteria

1. Person A's voice is cloned (Qwen; Minimax fallback ready).
2. Given text, the config speaks it in A's voice.
3. A spoken question can be transcribed to text.
4. The exact demo lines are pre-cached and play on demand if live TTS fails.

## Coordinate with Tony (one thing)

Agree the **voice handoff shape** early — i.e., "Tony, you'll plug my voice in as `<plugin/config X>`." Then he builds the room with a placeholder voice and swaps yours in with one change.

> ⚠️ **Verify against docs:** does Qwen/Minimax have a ready LiveKit TTS plugin, or do you/ Tony need a small **custom TTS node**? LiveKit supports both — check the current docs, don't assume.

## How to not wait on anyone

Fully independent — start now. Knock out the clone + cached lines fast, then move to your Moss-Retrieval PRD (`02`).

## SDKs you touch

**Qwen** (clone) · **Minimax** (TTS fallback) · STT plugin (e.g. Deepgram) · LiveKit TTS slot (with Tony). Ground every call in current docs — voice SDKs move fast.

## Next

`/gsd-plan-phase 3`, or build from the list. **Restart Claude Code first.**
