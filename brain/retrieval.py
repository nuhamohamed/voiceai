"""The brain's retrieval seam — the SHARED CONTRACT (don't change the signature alone).

    async retrieve(query_text, persona_id) -> list[RetrievedChunk]

Real implementation: queries Moss using MossClient. Each persona has its own index
(index_name == persona_id, e.g. "person_a"). Run brain/ingest.py once to populate
the indexes from data/<persona_id>_corpus.jsonl before the first retrieve() call.

Env vars required (from .env):
    MOSS_PROJECT_ID   — from portal.usemoss.dev
    MOSS_PROJECT_KEY  — from portal.usemoss.dev
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from moss import MossClient, QueryOptions

load_dotenv()

logger = logging.getLogger(__name__)

# Module-level singleton — one client and one set of loaded indexes per process.
_client: MossClient | None = None
_loaded_indexes: set[str] = set()


def _get_client() -> MossClient:
    global _client
    if _client is None:
        project_id = os.getenv("MOSS_PROJECT_ID")
        project_key = os.getenv("MOSS_PROJECT_KEY")
        if not project_id or not project_key:
            raise EnvironmentError(
                "MOSS_PROJECT_ID and MOSS_PROJECT_KEY must be set in .env. "
                "Get them from https://portal.usemoss.dev"
            )
        _client = MossClient(project_id, project_key)
    return _client


@dataclass
class RetrievedChunk:
    text: str     # the content used to ground the answer
    source: str   # "linear" | "slack" | "calendar"
    ref: str      # human-readable locator — shown in the on-screen 🔎 trace
    score: float  # retrieval relevance


async def retrieve(query_text: str, persona_id: str) -> list[RetrievedChunk]:
    """Query Moss for the persona's index and return the top relevant chunks.

    The index_name == persona_id (e.g. "person_a"). Run brain/ingest.py once
    to populate the index from data/<persona_id>_corpus.jsonl.
    Signature is fixed — Tony's agent imports this unchanged.
    """
    client = _get_client()

    # Load the index on first use for this persona; no-op on subsequent calls.
    if persona_id not in _loaded_indexes:
        logger.info("Loading Moss index '%s'", persona_id)
        await client.load_index(persona_id)
        _loaded_indexes.add(persona_id)

    results = await client.query(
        persona_id,
        query_text,
        QueryOptions(top_k=6, alpha=0.7),  # top_k=6: the demo's Q2 ("what's blocking it?")
        # ranks the real ENG-419/rotation chunks #3-#6, so top_k=3 dropped them and the
        # on-screen trace showed only the nearest near-duplicates. (Tony: cross-lane tweak
        # to unblock the Q2 moat trace — Nuha, please confirm; deduping MEL-* vs ENG-* in
        # the corpus would let this go back to 3.)
    )

    chunks: list[RetrievedChunk] = []
    for doc in (results.docs or []):
        meta = getattr(doc, "metadata", {}) or {}
        chunks.append(
            RetrievedChunk(
                text=(getattr(doc, "text", "") or "").strip(),
                source=meta.get("source", ""),
                ref=meta.get("ref", ""),
                score=round(float(getattr(doc, "score", 0.0)), 3),
            )
        )
    return chunks
