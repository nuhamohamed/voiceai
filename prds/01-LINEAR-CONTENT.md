# PRD 01 — Linear Content (Melody)

**Owner:** Melody · **Lane:** Person A's memory — the content
**You hand off:** `data/person_a_corpus.jsonl` → Nuha.

## Your outcome

Person A's real work context exists as a corpus file that's specific enough for the clone to answer the auth-migration questions with true, concrete detail. If the clone sounds real and specific in the demo, it's because your content held the specifics.

## The interface you must honor

The corpus file — `data/person_a_corpus.jsonl`, one JSON record per line:

```json
{"id": "lin-eng-412", "source": "linear|slack|calendar", "ref": "ENG-412 Auth migration", "text": "..."}
```

`ref` shows on screen in the retrieval trace, so keep it human-readable. That format is the only fixed thing — how you create the content is entirely yours.

## Done looks like

- The corpus file exists and is valid.
- It contains the specific detail the demo follow-up targets (the auth-migration **status** and its **blocker**) — so retrieval has a right answer to find.
- It reads as believable, real context.

## Worth knowing

- You're the **unblocker**: Nuha can't load Moss until a first version exists — ship an early draft fast (even a few records), then enrich.
- Short, one-fact-per-record entries retrieve better than long multi-topic ones.

## Hand-off

Drop `data/person_a_corpus.jsonl` to Nuha (PRD 02). That's the whole interface.
