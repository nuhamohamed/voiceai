# PRD 01 — Linear Content (Person A's memory)

**Owner:** Melody · **Roadmap:** Phase 2 (Brain, content half) · **Requirements:** BRN-01 (content side)
**Works alone against:** the corpus format in `00-FOUNDATION.md`. **Hands off:** `data/person_a_corpus.jsonl` → Nuha.

## Mission

Create the **real context** that makes the clone's answer specific and true. You author Person A's work life in **Linear** (the auth-migration ticket + related notes), then export it into the agreed **corpus file**. Your content *is* the moat — if the answer sounds specific and real, it's because your content had the specifics.

## What you build

1. **Author Person A's Linear content** — a believable, detailed slice of one project:
   - The **auth-migration ticket** (status, what's done, what's blocked, the specific blocker).
   - 2–4 related items: a couple of comments/updates, a related ticket, maybe a calendar item or Slack-style note.
   - Make it **specific** — names, dates, the exact blocker. Vague content → vague answer → dead demo.
2. **Export it to the corpus file** `data/person_a_corpus.jsonl`, one record per line, exactly in the format from `00-FOUNDATION.md`:
   ```json
   {"id": "...", "source": "linear|slack|calendar", "ref": "human locator", "text": "the content"}
   ```
   - `ref` is what shows on screen in the 🔎 trace — make it readable (e.g. `ENG-412 Auth migration`).
   - Export can be manual (copy Linear → jsonl) or via the Linear API — your call.

## Scope

**In:** the content + the corpus file. **Out:** Moss, retrieval, voice, the room (those are Nuha/Tony). You produce a **file**, nothing more.

## Success criteria

1. `data/person_a_corpus.jsonl` exists, valid format, one record per line.
2. The content contains the **specific detail** the scripted demo question asks about (so retrieval has a right answer to find).
3. At least one record is clearly the "auth-migration status" and one is the "blocker" the follow-up question targets.

## Design decisions that are yours

- How rich/realistic to make it (more good content = more convincing demo, to a point).
- The exact demo specifics — coordinate with Tony on the **scripted question** so your content has the matching answer.
- Manual export vs. Linear API (manual is totally fine for 2 personas).

## How to not wait on anyone

You're the **unblocker** — start immediately, you depend on no one (just the format spec). Get a first `person_a_corpus.jsonl` to Nuha fast (even 3–4 records), then enrich it.

## SDKs you touch

Linear (UI or API) for authoring. No Moss/voice/LiveKit. Ground any Linear API use in current docs.

## Next

`/gsd-plan-phase 2` (you + Nuha share Phase 2 — your plan is the content half), or just author + export.
