"""Unit tests for the Unsiloed chunk -> corpus-record mapping (brain/ingest_docs.py).

    python -m pytest tests/test_ingest_docs.py -q

These test the mapping LOGIC against the documented Unsiloed Parse response shape
(source: https://docs.unsiloed.ai/document-processing/parsing/response-format) —
chunk-level `embed` + segment-level `page_number`/`segment_type`. They do NOT hit
the live API; end-to-end proof comes from running `python -m brain.ingest_docs`
with a real UNSILOED_API_KEY (the "bake" step).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from brain.ingest_docs import chunk_to_record  # noqa: E402


# A chunk shaped like a real Unsiloed Parse response (response-format.md).
def _chunk(embed, segments, chunk_id="c1"):
    return {"chunk_id": chunk_id, "chunk_length": len(embed), "embed": embed,
            "segments": segments}


def _seg(segment_type, content, page_number=1):
    return {"segment_id": "s", "segment_type": segment_type, "content": content,
            "markdown": content, "page_number": page_number}


def test_maps_embed_to_text_and_builds_ref() -> None:
    chunk = _chunk(
        "## Rollback plan\nSet auth_oauth_enabled = false to revert to legacy sessions.",
        [_seg("SectionHeader", "Rollback plan", 2),
         _seg("Text", "Set auth_oauth_enabled = false ...", 2)],
    )
    rec = chunk_to_record(chunk, "auth-migration-rfc.pdf", 0)
    assert rec is not None
    assert rec["source"] == "doc"
    assert rec["text"].startswith("## Rollback plan")
    assert rec["ref"] == "auth-migration-rfc.pdf p.2 — Rollback plan"
    assert rec["id"] == "doc-auth-migration-rfc-0"  # stable positional id, not chunk_id


def test_drops_page_furniture_only_chunks() -> None:
    chunk = _chunk("", [_seg("PageHeader", "RFC-012", 1), _seg("PageFooter", "1", 1)])
    assert chunk_to_record(chunk, "doc.pdf", 0) is None


def test_falls_back_to_segments_when_embed_missing() -> None:
    chunk = {"chunk_id": "c9", "segments": [_seg("Text", "Body content here.", 3)]}
    rec = chunk_to_record(chunk, "doc.pdf", 0)
    assert rec is not None
    assert "Body content here." in rec["text"]
    assert rec["ref"] == "doc.pdf p.3"  # no heading segment -> no heading suffix


def test_moat_rollback_chunk_is_self_describing() -> None:
    # The planted demo question ("what's the rollback plan?") only lands if the
    # rollback content survives as one coherent, self-describing chunk.
    chunk = _chunk(
        "## Rollback plan\nRollback is a single action: set auth_oauth_enabled = false. "
        "The legacy Express/Redis middleware stays warm, so no redeploy and no forced logout.",
        [_seg("SectionHeader", "Rollback plan", 2)],
    )
    rec = chunk_to_record(chunk, "auth-migration-rfc.pdf", 0)
    blob = (rec["ref"] + " " + rec["text"]).lower()
    assert "rollback" in blob and "auth_oauth_enabled" in blob


if __name__ == "__main__":
    test_maps_embed_to_text_and_builds_ref()
    test_drops_page_furniture_only_chunks()
    test_falls_back_to_segments_when_embed_missing()
    test_moat_rollback_chunk_is_self_describing()
    print("OK — ingest_docs mapping tests pass")
