"""Contract + moat tests for retrieve() — run on the stub, and the target for Nuha's Moss impl.

    python -m pytest tests/ -q      (or)     python tests/test_retrieve.py

- test_contract_shape:   retrieve() returns list[RetrievedChunk] with {text, source, ref, score}.
- test_moat_right_chunk: the scripted demo follow-up surfaces the auth-migration blocker.
  This is the demo-saver: when Nuha swaps in real Moss, this test must still pass.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from brain.retrieval import retrieve, RetrievedChunk  # noqa: E402


def test_contract_shape() -> None:
    chunks = asyncio.run(retrieve("what's blocking the auth migration?", "person_a"))
    assert isinstance(chunks, list) and chunks, "retrieve() must return >=1 chunk"
    c = chunks[0]
    assert isinstance(c, RetrievedChunk)
    for field in ("text", "source", "ref", "score"):
        assert hasattr(c, field), f"RetrievedChunk missing {field}"


def test_moat_right_chunk() -> None:
    chunks = asyncio.run(retrieve("what is blocking the auth migration?", "person_a"))
    top = chunks[0]
    blob = (top.ref + " " + top.text).lower()
    assert "auth" in blob, f"top chunk not about auth: {top.ref}"
    assert "block" in blob or "ttl" in blob, f"top chunk doesn't name the blocker: {top.text}"


def test_moat_unsiloed_doc_chunk() -> None:
    # The sponsor moment: the Unsiloed-parsed product doc must dominate retrieval
    # for the release question, so the on-screen trace visibly cites the PDF
    # (source="doc") rather than Slack/Linear. Requires brain/ingest_docs.py +
    # brain/ingest to have been run (data/person_a_docs.jsonl baked into Moss).
    chunks = asyncio.run(retrieve("What shipped in the last release?", "person_a"))
    doc_chunks = [c for c in chunks if c.source == "doc"]
    assert len(doc_chunks) >= 3, f"PDF should dominate; got sources {[c.source for c in chunks]}"
    assert any("hippo-product-doc" in c.ref for c in chunks), "no hippo-product-doc citation in trace"


if __name__ == "__main__":
    test_contract_shape()
    test_moat_right_chunk()
    test_moat_unsiloed_doc_chunk()
    print("OK — retrieval contract + moat tests pass")
