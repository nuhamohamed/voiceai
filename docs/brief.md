# Standup Proxies — Conversational AI Hackathon (Moss, Jun 6–7, 2026)

## What we're building
An ambient AI agent that joins a live meeting as a proxy for an absent teammate.
When someone in the call asks a question about that teammate's work, the agent
retrieves their context (Linear tickets, Slack messages, product docs) from Moss
and answers in real time using the teammate's cloned voice.

## Demo threads
1. **Stand in for the absent expert.** PM asks "what's the status of the auth
   migration?" Agent retrieves the absent engineer's Linear tickets + Slack
   context, answers in their cloned voice with specifics.
2. **Living product memory (stretch).** Someone asks "what shipped in the last
   release?" Agent retrieves from a product doc indexed in Moss, answers with
   versions, features, known issues.

## Architecture
- **LiveKit** — real-time room; agent joins as a participant.
- **Moss** — per-user semantic index of Linear + Slack + docs.
- **Qwen** — voice clone for the absent teammate.
- **Minimax** — neutral TTS fallback.
- **Unsiloed** — parses PDF product doc into Moss (stretch).
- **TrueFoundry** — LLM gateway.

## Scope cuts (locked)
- No screen/OS watching.
- No autonomous agent-to-agent chatter.
- No OAuth, no multi-tenant. Hardcoded personas.
- No custom UI. Demo runs in LiveKit's playground + a Slack channel for summaries.

## Data sources
- Linear: fresh free workspace, seeded tickets, personal API key.
- Slack ingestion: fake JSON file of recent messages, indexed into Moss.
- Slack output: real incoming webhook to a fresh free Slack workspace.
- Product doc: hand-written mock PDF/markdown (stretch).

## PRs
- #1 Linear ingestion — fetch tickets by assignee, chunk, index into Moss.
- #2 Slack pieces — load fake messages into Moss; post summaries via webhook.
- #3 Product doc retrieval (stretch) — parse PDF via Unsiloed, index into Moss.
