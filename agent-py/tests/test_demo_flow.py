"""Mic-free proof of the two-question demo flow (docs/demo-script.md).

This proves everything about the demo that does NOT require a live room/mic:

  1. Routing — the REAL production hook `Assistant.on_user_turn_completed`
     selects the right cached WAV per question and falls through off-script:
       - a status question  -> update.wav  + StopResponse (LLM suppressed)
       - a blocker question -> blocker.wav + StopResponse (LLM suppressed)
       - an off-script question -> no StopResponse, retrieve() NOT called
     We drive the actual hook (no refactor of agent.py) inside a ROOMLESS
     AgentSession, exactly like tests/test_agent.py. `Assistant()` defaults
     room=None, so `_publish_moss_context` returns early — no data-channel to
     mock. We stub `agent.retrieve` (no Moss/network here) and `agent.wav_frames`
     (records the WAV path the branch chose) and no-op `session.say` (a 26-32s
     cached WAV must not actually play in a unit test). StopResponse-vs-no-raise
     is the branch discriminator; the recorded WAV name proves WHICH branch.

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


def _recording_wav_frames(recorded: list[str]):
    """Stand-in for playback.wav_frames: record the chosen WAV path, yield nothing.

    The branch builds say(audio=wav_frames(wav)); we capture `wav` synchronously
    at call time, independent of whether the (stubbed) say() ever iterates it.
    """

    def _factory(path: str):
        recorded.append(path)

        async def _gen():  # an async generator that yields no frames
            return
            yield  # pragma: no cover  (marks this a generator)

        return _gen()

    return _factory


async def _run_turn(question: str, monkeypatch) -> dict:
    """Drive the real on_user_turn_completed for `question` in a roomless session.

    Returns {"stopped": bool, "wavs": [basenames], "retrieve_called": bool}.
    """
    recorded: list[str] = []
    fake_retrieve = AsyncMock(return_value=[])

    monkeypatch.setattr(agent_mod, "retrieve", fake_retrieve)
    monkeypatch.setattr(agent_mod, "wav_frames", _recording_wav_frames(recorded))

    say_mock = AsyncMock()
    async with AgentSession() as session:
        assistant = agent_mod.Assistant()  # room=None -> _publish_moss_context no-ops
        await session.start(assistant)
        # A 26-32s cached WAV must not actually play in a unit test. Hold our own
        # reference so we can read call_args AFTER the session context closes
        # (assistant.session is only accessible while the activity is running).
        assistant.session.say = say_mock

        msg = ChatMessage(role="user", content=[question])
        stopped = False
        try:
            await assistant.on_user_turn_completed(ChatContext(), msg)
        except StopResponse:
            stopped = True

    # The spoken transcript is the first positional arg to session.say(...). It
    # must match demo-script.md so the on-screen transcript lines up with the WAV.
    spoken = ""
    if say_mock.call_args is not None:
        spoken = say_mock.call_args.args[0]

    return {
        "stopped": stopped,
        "wavs": [pathlib.Path(p).name for p in recorded],
        "retrieve_called": fake_retrieve.called,
        "spoken": spoken,
    }


# ---------------------------------------------------------------------------
# 1. Routing — the real production hook picks the right WAV / falls through
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_status_question_routes_to_update_wav(monkeypatch) -> None:
    out = await _run_turn(Q_STATUS, monkeypatch)
    assert out["stopped"], "status question must raise StopResponse (suppress the LLM)"
    assert out["wavs"] == ["update.wav"], f"expected update.wav, got {out['wavs']}"
    assert out["retrieve_called"], "status branch should run retrieve() for the trace"
    # Spoken transcript matches the Q1 line in demo-script.md (drives the on-screen text).
    assert "PR #847" in out["spoken"] and "ENG-419" in out["spoken"]


@pytest.mark.asyncio
async def test_blocker_question_routes_to_blocker_wav(monkeypatch) -> None:
    out = await _run_turn(Q_BLOCKER, monkeypatch)
    assert out["stopped"], "blocker question must raise StopResponse (suppress the LLM)"
    assert out["wavs"] == ["blocker.wav"], f"expected blocker.wav, got {out['wavs']}"
    assert out["retrieve_called"], "blocker branch should run retrieve() for the trace"
    # Spoken transcript matches the Q2 moat line in demo-script.md.
    assert "ENG-419" in out["spoken"] and "reuse detection" in out["spoken"]


@pytest.mark.asyncio
async def test_offscript_question_falls_through(monkeypatch) -> None:
    out = await _run_turn(Q_OFFSCRIPT, monkeypatch)
    assert not out["stopped"], "off-script question must NOT raise StopResponse"
    assert out["wavs"] == [], f"off-script must play no cached WAV, got {out['wavs']}"
    assert not out["retrieve_called"], (
        "off-script must not run the cached-branch retrieve(); it falls through "
        "to the live LLM + search_knowledge path"
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
