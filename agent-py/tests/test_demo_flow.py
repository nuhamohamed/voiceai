"""Mic-free proof of the two-question demo flow (docs/demo-script.md).

This proves everything about the demo that does NOT require a live room/mic:

  1. Routing (FULLY LIVE) — the REAL production hook
     `Assistant.on_user_turn_completed` intercepts NOTHING. Every question,
     including the former demo anchors (status, blocker), falls through to the
     live LLM + search_knowledge path: the hook raises no StopResponse, speaks
     no cached WAV, and runs no retrieve() of its own (retrieval now happens
     inside search_knowledge). We drive the actual hook inside a ROOMLESS
     AgentSession, exactly like tests/test_agent.py. `Assistant()` defaults
     room=None, so `_publish_moss_context` returns early — no data-channel to
     mock. We stub `agent.retrieve` (no Moss/network here) and no-op
     `session.say`; the hook must touch neither.

  2. Moat retrieval (REAL Moss) — the bare Q2 demo string the production hook
     actually passes, `"what's actually blocking it?"`, retrieves chunks whose
     combined text contains "ENG-419" or "refresh-token rotation". (top_k=6 in
     brain/retrieval.py was tuned for exactly this; verified live via
     scripts/harness.py.) Skips ONLY if Moss is unreachable/unconfigured.

  3. Payload shape — build_moss_context_payload(...) matches the frontend
     contract: type "moss_context"; data.matches[] of {text, score,
     metadata.ref, metadata.source}.

  4. WAV decode — blocker.wav and update.wav each decode via playback.wav_frames
     to exactly one well-formed rtc.AudioFrame (robust to the bogus data-chunk
     header documented in playback.py).

Async style matches the project's pytest-asyncio config (asyncio_mode=auto in
pyproject.toml); @pytest.mark.asyncio is added explicitly to mirror
tests/test_agent.py + tests/test_integration.py.
"""

from __future__ import annotations

import pathlib
import sys
from unittest.mock import AsyncMock

import pytest

_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
)  # repo root: brain.retrieval, personas, voice, audio/
_SRC = (
    pathlib.Path(__file__).resolve().parents[1] / "src"
)  # agent-py/src: agent, grounding, playback
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from brain.retrieval import RetrievedChunk, retrieve  # noqa: E402
from livekit.agents import (  # noqa: E402
    AgentSession,
    ChatContext,
    ChatMessage,
    StopResponse,
)

import agent as agent_mod  # noqa: E402  the module under test (production hook)
from grounding import build_moss_context_payload  # noqa: E402
from playback import wav_frames  # noqa: E402

_AUDIO_DIR = _ROOT / "audio" / "demo"

# The two scripted demo questions, verbatim from docs/demo-script.md, plus an
# off-script control. The blocker string is exactly what the production hook
# passes to retrieve() (new_message.text_content), so item 2 is faithful.
Q_STATUS = "what's the status of the auth migration?"
Q_BLOCKER = "what's actually blocking it?"
Q_OFFSCRIPT = "how are you feeling today?"


async def _run_turn(question: str, monkeypatch) -> dict:
    """Drive the real on_user_turn_completed for `question` in a roomless session.

    Returns {"stopped": bool, "said": bool, "retrieve_called": bool}. Fully-live
    means all three are False for every question — the hook intercepts nothing.
    """
    fake_retrieve = AsyncMock(return_value=[])
    monkeypatch.setattr(agent_mod, "retrieve", fake_retrieve)

    say_mock = AsyncMock()
    async with AgentSession() as session:
        assistant = agent_mod.Assistant()  # room=None -> _publish_moss_context no-ops
        await session.start(assistant)
        assistant.session.say = say_mock

        msg = ChatMessage(role="user", content=[question])
        stopped = False
        try:
            await assistant.on_user_turn_completed(ChatContext(), msg)
        except StopResponse:
            stopped = True

    return {
        "stopped": stopped,
        "said": say_mock.called,
        "retrieve_called": fake_retrieve.called,
    }


# ---------------------------------------------------------------------------
# 1. Routing (FULLY LIVE) — the hook intercepts nothing; every question
#    (status, blocker, off-script) falls through to the live LLM path.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("question", [Q_STATUS, Q_BLOCKER, Q_OFFSCRIPT])
@pytest.mark.asyncio
async def test_every_question_goes_live(question: str, monkeypatch) -> None:
    out = await _run_turn(question, monkeypatch)
    assert not out["stopped"], (
        f"{question!r}: hook must not raise StopResponse (the LLM must answer)"
    )
    assert not out["said"], f"{question!r}: hook must speak no cached answer"
    assert not out["retrieve_called"], (
        f"{question!r}: hook must run no cached-branch retrieve() — retrieval now "
        "happens inside the search_knowledge tool on the live path"
    )


# ---------------------------------------------------------------------------
# 2. Moat retrieval (REAL Moss) — the bare Q2 string the hook actually passes
#    surfaces the ENG-419 / refresh-token-rotation blocker theme.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_blocker_question_retrieves_eng419_from_moss() -> None:
    try:
        chunks = await retrieve(Q_BLOCKER, "person_a")
    except Exception as exc:  # Moss unreachable / unconfigured (env or network)
        pytest.skip(f"Moss not available for live retrieval: {exc!r}")

    assert len(chunks) >= 1, "expected at least one retrieved chunk"
    combined = " ".join((c.text or "") for c in chunks).lower()
    assert "eng-419" in combined or "refresh-token rotation" in combined, (
        f"blocker theme not retrieved for the bare Q2 string; "
        f"refs={[c.ref for c in chunks]}"
    )


# ---------------------------------------------------------------------------
# 3. Payload shape — build_moss_context_payload matches the frontend contract
# ---------------------------------------------------------------------------
def test_build_moss_context_payload_matches_frontend_shape() -> None:
    chunks = [
        RetrievedChunk(
            text="Implement sliding-window refresh-token rotation per Ivan's review.",
            source="linear",
            ref="ENG-419",
            score=0.902,
        ),
        RetrievedChunk(
            text="Ivan wants reuse detection that invalidates the token family.",
            source="slack",
            ref="#security",
            score=0.74,
        ),
    ]
    payload = build_moss_context_payload(Q_BLOCKER, chunks)

    assert payload["type"] == "moss_context"
    data = payload["data"]
    assert data["query"] == Q_BLOCKER
    assert isinstance(data["matches"], list) and len(data["matches"]) == 2

    m0 = data["matches"][0]
    assert m0["text"]  # non-empty text the panel renders
    assert isinstance(m0["score"], (int, float))
    assert m0["metadata"]["ref"] == "ENG-419"
    assert m0["metadata"]["source"] == "linear"


# ---------------------------------------------------------------------------
# 4. WAV decode — both demo WAVs decode to one well-formed AudioFrame
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["update", "blocker"])
@pytest.mark.asyncio
async def test_demo_wav_decodes_one_valid_frame(name: str) -> None:
    path = _AUDIO_DIR / f"{name}.wav"
    assert path.exists(), f"missing demo WAV: {path}"

    frames = [f async for f in wav_frames(str(path))]
    assert len(frames) == 1, "wav_frames should yield exactly one AudioFrame"
    frame = frames[0]
    assert frame.samples_per_channel > 0
    # rtc.AudioFrame.data is a memoryview of int16 (itemsize=2). len() counts
    # elements (samples*channels); .nbytes is the raw byte count (== *2).
    n_samples = frame.samples_per_channel * frame.num_channels
    assert len(frame.data) == n_samples
    assert frame.data.nbytes == n_samples * 2
