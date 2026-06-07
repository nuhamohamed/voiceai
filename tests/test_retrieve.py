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


if __name__ == "__main__":
    test_contract_shape()
    test_moat_right_chunk()
    print("OK — retrieval contract + moat tests pass (stub)")
