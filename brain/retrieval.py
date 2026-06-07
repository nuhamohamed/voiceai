"""The brain's retrieval seam — the SHARED CONTRACT (don't change the signature alone).

    async retrieve(query_text, persona_id) -> list[RetrievedChunk]

This is a STUB: it does naive keyword matching over the persona's corpus file so the
text harness and the LiveKit agent work end-to-end TODAY — no Moss, no keys, stdlib only.

Nuha replaces the *internals* with Moss (MossClient.query / load_index, per the
Moss x LiveKit page) — the signature and return type stay identical, so Tony's agent
and the harness keep working with a one-line import swap.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

DATA_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "data")


@dataclass
class RetrievedChunk:
    text: str     # the content used to ground the answer
    source: str   # "linear" | "slack" | "calendar"
    ref: str      # human-readable locator — shown in the on-screen 🔎 trace
    score: float  # retrieval relevance


def _corpus_path(persona_id: str) -> str:
    """Prefer the persona's real corpus (Melody's), fall back to the shipped sample."""
    real = os.path.join(DATA_DIR, f"{persona_id}_corpus.jsonl")
    return real if os.path.exists(real) else os.path.join(DATA_DIR, "sample_corpus.jsonl")


def _load_corpus(path: str) -> list[dict]:
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _tokens(text: str) -> set[str]:
    return {w.strip(".,?!:;").lower() for w in text.split() if w.strip(".,?!:;")}


async def retrieve(query_text: str, persona_id: str) -> list[RetrievedChunk]:
    """STUB retrieval. Returns the top corpus chunks by naive keyword overlap.

    Real version (Nuha): query Moss for `persona_id`'s index and map hits ->
    RetrievedChunk(text, source, ref, score). Keep this exact signature.
    """
    rows = _load_corpus(_corpus_path(persona_id))
    query_words = _tokens(query_text)
    scored: list[tuple[float, dict]] = []
    for row in rows:
        overlap = len(query_words & _tokens(row.get("text", "")))
        scored.append((overlap / (len(query_words) or 1), row))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    hits = [(s, r) for s, r in scored if s > 0][:3] or scored[:1]
    return [
        RetrievedChunk(
            text=r.get("text", ""),
            source=r.get("source", ""),
            ref=r.get("ref", ""),
            score=round(s, 3),
        )
        for s, r in hits
    ]
