# Standup Proxy — Workstream PRDs (split for 3)

This folder is **the structure for splitting the build across the 3-person team.** Each PRD is self-contained: a teammate can pick one up, read it top to bottom, and start planning their details without reading the others.

> Full project context lives in `../.planning/PROJECT.md`, `../.planning/REQUIREMENTS.md`, `../.planning/ROADMAP.md`. These PRDs are the per-owner handoff slices of that roadmap.

## Demo north star (what every workstream serves)

In a live standup, a follow-up question to an **absent teammate's clone** → it **visibly retrieves from Moss** and **answers in that person's real voice with the actual specifics**. If everything else fails, *that moment* must work — it's the moat.

## The split

| PRD | Workstream | Owner | Maps to Roadmap | Build against |
|-----|-----------|-------|-----------------|---------------|
| `00-FOUNDATION.md` | Shared scaffold + the `handle_turn` contract | **One person, FIRST** | Phase 1 | — |
| `01-BRAIN.md` | Context retrieval from Moss (the moat) | Owner A | Phase 2 | the contract |
| `02-VOICE.md` | Cloned voice: STT in / TTS out | Owner B | Phase 3 | the contract (mock brain) |
| `03-LIVE.md` | LiveKit room + manager↔teammate exchange + Slack summary | Owner C | Phase 4 | the contract + integrates A & B |

## How parallelism works (read this once)

The three workstreams are **not** blocked on each other — they're all blocked only on **one thing: the `handle_turn` contract** (defined in `00-FOUNDATION.md`). The plan:

1. **One person scaffolds Foundation first** (Phase 1). Small, fast: repo, `.env`, the contract module, persona config, a text harness. This produces a *real* importable `handle_turn` + a `handle_turn` **stub**.
2. **Meanwhile**, the other two owners read the contract spec in `00-FOUNDATION.md` and **plan their PRDs against the paper contract** — nobody waits.
3. Once Foundation lands (just the contract + stub is enough), all three go **fully parallel**. Voice and Live import the **stub** `handle_turn` until Brain ships the real one — then it's a drop-in swap (the contract doesn't change).

```
        ┌──────────────────────────────┐
        │ 00 FOUNDATION (one person)    │  ← contract + stub, FIRST
        │  handle_turn(text, persona)   │
        └───────────────┬──────────────┘
                        │ (everyone imports this)
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   01 BRAIN        02 VOICE        03 LIVE
   (real brain)   (mock→real)    (mock→real, assembles A+B)
```

## The rule that keeps the swap free

**Nobody changes the contract signature unilaterally.** If you think `handle_turn` needs to change, raise it to the team — it's the one shared surface. Everything else inside your workstream is yours to design.

## Source-driven, no hallucinated SDKs

Moss, LiveKit, Qwen, Minimax — **ground every SDK call in current docs** (use the `source-driven-development` skill / context7 / the `livekit-docs` MCP). Do not invent API names. This is in the project constraints for a reason.

## How to plan your details (per owner)

Two options once you own a PRD:
- **GSD-native:** run `/gsd-plan-phase <N>` for your phase (`2` Brain, `3` Voice, `4` Live) → GSD interviews you and produces a detailed task-level `PLAN.md`. *(Restart Claude Code first — GSD was just installed.)*
- **Lightweight:** plan directly in your PRD's "Suggested slices" section and just build.

## Go / no-go (whole team)

If the **spine** (Brain returning the right answer from real context, in text) isn't landing after the first build block → fall back to **Slack-summary-only** (`01-BRAIN.md` → FBK-01) and stop chasing live voice. Protect the demo.
