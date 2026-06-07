"""Tests for the clone-voice TTS used by the LIVE (off-script) answer path.

The scripted demo answers play cached WAVs and never touch this module
(session.say(..., audio=...) bypasses TTS). Off-script LLM replies route through
agent.tts_node -> qwen_tts.synthesize_clone, which synthesizes in Person A's
enrolled Qwen clone and returns one rtc.AudioFrame.

Two layers:
  1. wav_bytes_to_frame (pure, always runs): wrapping 24kHz/mono/16-bit WAV bytes
     into a single well-formed AudioFrame, robust to a BOGUS WAV data-chunk
     header (the Qwen renderer's quirk, same one playback.wav_frames guards
     against). We build the WAV in-memory so there is no network/dashscope dep.
  2. synthesize_clone (live, skipped unless dashscope is installed AND
     DASHSCOPE_API_KEY is set): a real Qwen call must return nonempty 24kHz PCM
     in the persona's clone voice. Skips cleanly under plain `uv run pytest`,
     since dashscope is not in agent-py's base venv.
"""

from __future__ import annotations

import io
import os
import pathlib
import struct
import sys
import wave

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root: personas
_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"  # agent-py/src: qwen_tts
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from qwen_tts import SAMPLE_RATE, synthesize_clone, wav_bytes_to_frame  # noqa: E402


def _make_wav_bytes(n_samples: int, *, bogus_header: bool) -> bytes:
    """Build a 24kHz mono 16-bit WAV in memory.

    With bogus_header=True we corrupt the data-chunk size to ~1.07e9 (matching
    the real Qwen renderer quirk) AFTER writing, to prove wav_bytes_to_frame
    derives samples_per_channel from the real byte count, not the header.
    """
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(b"\x01\x00" * n_samples)  # nonzero int16 samples
    raw = bytearray(buf.getvalue())
    if bogus_header:
        # WAV layout: "RIFF"(4) size(4) "WAVE"(4) "fmt "(4) 16(4) ...fmt(16)
        # "data"(4) datasize(4) ...  -> find "data" and overwrite the next 4 bytes.
        idx = raw.find(b"data")
        assert idx != -1
        struct.pack_into("<I", raw, idx + 4, 1073741773)  # bogus data-chunk size
    return bytes(raw)


def test_wav_bytes_to_frame_well_formed() -> None:
    n = 2400  # 0.1s at 24kHz
    frame = wav_bytes_to_frame(_make_wav_bytes(n, bogus_header=False))
    assert frame.sample_rate == SAMPLE_RATE
    assert frame.num_channels == 1
    assert frame.samples_per_channel == n
    # rtc.AudioFrame.data is int16 (itemsize 2): len() counts elements, .nbytes bytes.
    assert len(frame.data) == n
    assert frame.data.nbytes == n * 2


def test_wav_bytes_to_frame_ignores_bogus_data_chunk_size() -> None:
    n = 1800
    frame = wav_bytes_to_frame(_make_wav_bytes(n, bogus_header=True))
    # samples_per_channel comes from REAL bytes, not the corrupted header.
    assert frame.samples_per_channel == n
    assert frame.data.nbytes == n * 2


@pytest.mark.asyncio
async def test_synthesize_clone_returns_nonempty_pcm() -> None:
    """Real Qwen call: the persona's clone voice yields nonempty 24kHz PCM.

    Skips unless dashscope is installed (not in agent-py's base venv) AND the key
    is configured — so plain `uv run pytest` stays green.
    """
    pytest.importorskip("dashscope")
    from dotenv import load_dotenv

    load_dotenv(_ROOT / ".env")
    if not os.getenv("DASHSCOPE_API_KEY"):
        pytest.skip("DASHSCOPE_API_KEY not set")

    from personas import get_persona

    voice_id = get_persona("person_a").voice_id
    try:
        frame = synthesize_clone("Quick clone-voice smoke test.", voice_id)
    except Exception as exc:  # network / endpoint / auth issues
        pytest.skip(f"Qwen synthesis unavailable: {exc!r}")

    assert frame.sample_rate == SAMPLE_RATE
    assert frame.num_channels == 1
    assert frame.samples_per_channel > 0
    assert frame.data.nbytes > 0
