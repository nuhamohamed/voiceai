"""Pure adapters: our RetrievedChunk -> LLM grounding text + the frontend's moss_context payload.

Keeping these pure (no I/O) makes them unit-testable and keeps agent.py thin.
The moss_context shape MUST match frontend/hooks/useMossContextEvents.ts: a
data.matches list of {text, score?, metadata?}. We put ref/source in metadata so
the on-screen panel can show "ENG-412 (linear)".
"""
from __future__ import annotations

from datetime import datetime, timezone


def format_chunks_for_llm(chunks) -> str:
    """One grounded block per chunk, labelled by ref so the LLM can cite it."""
    parts = [f"[{c.ref}] {c.text}".strip() for c in chunks if getattr(c, "text", "").strip()]
    return "\n\n".join(parts) if parts else "No relevant context was found for that question."


def build_moss_context_payload(query: str, chunks) -> dict:
    """Shape the trace exactly as the frontend panel expects."""
    matches = []
    for c in chunks:
        entry = {"text": (c.text or "").strip(), "score": float(c.score)}
        entry["metadata"] = {"ref": c.ref, "source": c.source}
        matches.append(entry)
    return {
        "type": "moss_context",
        "data": {
            "query": query,
            "matches": matches,
            "timestamp": datetime.now(timezone.utc).timestamp(),  # epoch seconds; frontend *1000
        },
    }
