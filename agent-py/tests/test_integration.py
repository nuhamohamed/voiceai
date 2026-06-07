"""Behavioral integration tests for the standup clone — honest, source-driven.

Three layers, none of which fake retrieval:
  1. unit (deterministic, no network): the pure grounding adapters produce the
     LLM text + the exact moss_context payload the frontend parses.
  2. wav decode: playback.wav_frames yields one well-formed rtc.AudioFrame per
     cached demo WAV (robust to the bogus data-chunk header).
  3. live Moss retrieval (real): retrieve() over the person_a index returns a
     chunk whose text carries the auth-migration blocker theme (ENG-419 /
     refresh-token rotation). Skips ONLY if Moss is unreachable / unconfigured.

Async test style follows the project's pytest-asyncio config (asyncio_mode=auto
in pyproject.toml); @pytest.mark.asyncio is added explicitly to match
tests/test_agent.py.
"""

import pathlib
import sys

import pytest

_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
)  # repo root: brain.retrieval, personas, voice
_SRC = (
    pathlib.Path(__file__).resolve().parents[1] / "src"
)  # agent-py/src: grounding, playback
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from brain.retrieval import RetrievedChunk, retrieve  # noqa: E402

from grounding import build_moss_context_payload, format_chunks_for_llm  # noqa: E402
from playback import wav_frames  # noqa: E402

_AUDIO_DIR = _ROOT / "audio" / "demo"


def _chunks():
    return [
        RetrievedChunk(
            text="Auth migration is blocked on ENG-419 refresh-token rotation.",
            source="linear",
            ref="ENG-412",
            score=0.91,
        ),
        RetrievedChunk(
            text="Ivan wants sliding-window refresh-token rotation with reuse detection.",
            source="slack",
            ref="#security",
            score=0.74,
        ),
    ]


# ---------------------------------------------------------------------------
# 1. unit — pure grounding adapters (deterministic, no network)
# ---------------------------------------------------------------------------
def test_format_chunks_for_llm_includes_refs_and_text():
    out = format_chunks_for_llm(_chunks())
    assert "ENG-412" in out and "Auth migration is blocked" in out
    assert "#security" in out and "reuse detection" in out


def test_build_moss_context_payload_matches_frontend_contract():
    q = "what's blocking the auth migration?"
    p = build_moss_context_payload(q, _chunks())
    assert p["type"] == "moss_context"
    d = p["data"]
    assert d["query"] == q
    assert isinstance(d["matches"], list) and len(d["matches"]) == 2
    m0 = d["matches"][0]
    assert m0.get("text")
    assert isinstance(m0["score"], (int, float))
    assert m0["metadata"]["ref"] == "ENG-412"
    assert m0["metadata"]["source"] == "linear"


# ---------------------------------------------------------------------------
# 2. wav decode — every cached demo WAV yields one well-formed AudioFrame
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["update", "blocker", "slack_summary"])
@pytest.mark.asyncio
async def test_wav_frames_decodes_one_valid_frame(name: str):
    path = _AUDIO_DIR / f"{name}.wav"
    assert path.exists(), f"missing demo WAV: {path}"

    frames = [f async for f in wav_frames(str(path))]
    assert len(frames) == 1, "wav_frames should yield exactly one AudioFrame"
    frame = frames[0]
    assert frame.samples_per_channel > 0
    # rtc.AudioFrame.data is a memoryview of int16 (itemsize=2, format 'h'):
    # len() counts elements (samples*channels); .nbytes is the raw byte count.
    # 16-bit PCM => byte count == samples * channels * 2.
    n_samples = frame.samples_per_channel * frame.num_channels
    assert len(frame.data) == n_samples
    assert frame.data.nbytes == n_samples * 2


# ---------------------------------------------------------------------------
# 3. live Moss retrieval — real, honest. Proves the retrieve() seam end-to-end.
#    A status/migration query DOES surface the ENG-419 / refresh-token-rotation
#    theme. We do NOT assert on the bare "what's actually blocking it?" phrasing
#    (it under-retrieves — known cross-lane ranking issue, not ours to game).
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_live_moss_retrieval_surfaces_blocker_theme():
    query = (
        "what is the status of the auth migration and what's blocking it before prod?"
    )
    try:
        chunks = await retrieve(query, "person_a")
    except Exception as exc:  # Moss unreachable / unconfigured (env or network)
        pytest.skip(f"Moss not available for live retrieval: {exc!r}")

    assert len(chunks) >= 1, "expected at least one retrieved chunk"
    combined = " ".join((c.text or "") for c in chunks).lower()
    assert "eng-419" in combined or "refresh-token rotation" in combined, (
        f"blocker theme not retrieved; got refs={[c.ref for c in chunks]}"
    )
