import pathlib
import sys

_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
)  # repo root: brain.retrieval, personas, voice
_SRC = (
    pathlib.Path(__file__).resolve().parents[1] / "src"
)  # agent-py/src: grounding, playback
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from brain.retrieval import RetrievedChunk  # noqa: E402

from grounding import build_moss_context_payload, format_chunks_for_llm  # noqa: E402


def _chunks():
    return [
        RetrievedChunk(
            text="Auth migration blocked on ENG-419.",
            source="linear",
            ref="ENG-412",
            score=0.91,
        ),
        RetrievedChunk(
            text="Ivan wants refresh-token rotation.",
            source="slack",
            ref="#security",
            score=0.74,
        ),
    ]


def test_format_chunks_for_llm_joins_ref_and_text():
    out = format_chunks_for_llm(_chunks())
    assert "ENG-412" in out and "Auth migration blocked" in out
    assert "#security" in out


def test_format_chunks_for_llm_empty_is_honest():
    assert "No relevant" in format_chunks_for_llm([])


def test_build_payload_matches_frontend_contract():
    p = build_moss_context_payload("why is auth blocked?", _chunks())
    assert p["type"] == "moss_context"
    d = p["data"]
    assert d["query"] == "why is auth blocked?"
    assert isinstance(d["matches"], list) and len(d["matches"]) == 2
    m0 = d["matches"][0]
    assert m0["text"] == "Auth migration blocked on ENG-419."
    assert m0["score"] == 0.91
    assert m0["metadata"]["ref"] == "ENG-412"
    assert m0["metadata"]["source"] == "linear"
    assert isinstance(d["timestamp"], (int, float))  # epoch seconds
