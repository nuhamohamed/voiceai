"""Synthesize speech in Person A's enrolled Qwen voice clone for the LIVE path.

The scripted demo answers play pre-rendered WAVs (see agent.py's
`on_user_turn_completed` + `playback.wav_frames`). OFF-script answers, however,
are generated live by the LLM and would otherwise be spoken by the
AgentSession's stock `inference.TTS` — a generic voice. That switch is jarring.
This module reuses the SAME enrolled Qwen clone so the off-script voice matches
the scripted one. `agent.py`'s `tts_node` override calls `synthesize_clone()`.

Why `MultiModalConversation` (not `tts_v2.SpeechSynthesizer`)?
  This is the path that rendered the cached demo WAVs (see voice/clone.py). It is
  the only one PROVEN to work for the clone model + this enrolled voice id on the
  international endpoint. `tts_v2.SpeechSynthesizer` uses a WebSocket transport and
  returns `ModelNotFound` for `qwen3-tts-vc-2026-01-22` against that endpoint
  (verified live), so we deliberately do NOT use it.

Audio format: `MultiModalConversation` returns a URL to a WAV that is 24000 Hz,
mono, 16-bit PCM — IDENTICAL to the cached demo WAVs (verified). We download it
and wrap the PCM samples into a single `rtc.AudioFrame`, deriving
`samples_per_channel` from the real byte count (the Qwen WAV header carries a
BOGUS data-chunk size — same quirk documented in playback.py).

DEPENDENCY NOTE: `dashscope`/`httpx` are NOT in agent-py's venv (they live in the
repo-root voice/ environment). They are imported LAZILY inside `synthesize_clone()`
so that `import agent` / the test suite / ruff all work without them. The live
clone-voice path requires `dashscope` to be installed in the agent runtime env
(e.g. `uv --directory agent-py add dashscope httpx`) — a human follow-up, since
this lane may not edit pyproject.toml.

LATENCY NOTE: `MultiModalConversation.call(..., stream=False)` is one-shot
(synthesize-then-download), so a live answer pauses briefly before speaking.
Off-script replies are kept to 1-3 sentences (see agent.py instructions) to keep
that pause small. A streaming/callback mode could reduce it further, but the
clone model is not served over the streaming WebSocket transport (see above).
"""

from __future__ import annotations

import io
import os
import pathlib
import wave

from livekit import rtc

# DASHSCOPE_API_KEY lives in the repo-root .env (agent.py only loads .env.local).
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

# International endpoint — matches voice/clone.py, where the clone was enrolled
# and the demo WAVs were rendered.
_BASE_HTTP_API_URL = "https://dashscope-intl.aliyuncs.com/api/v1"
_TTS_MODEL = "qwen3-tts-vc-2026-01-22"  # must match the enrollment target_model

# The clone is 24kHz mono 16-bit PCM; cached demo WAVs match this exactly.
SAMPLE_RATE = 24000
NUM_CHANNELS = 1
_SAMPLE_WIDTH = 2  # bytes per int16 sample


def _api_key() -> str:
    """Read DASHSCOPE_API_KEY, loading the repo-root .env if needed."""
    key = os.getenv("DASHSCOPE_API_KEY")
    if not key:
        try:
            from dotenv import load_dotenv

            load_dotenv(_REPO_ROOT / ".env")
        except Exception:
            pass
        key = os.getenv("DASHSCOPE_API_KEY")
    if not key:
        raise RuntimeError(
            "DASHSCOPE_API_KEY is not set (expected in repo-root .env). "
            "Cannot synthesize the clone voice for the off-script path."
        )
    return key


def wav_bytes_to_frame(wav_bytes: bytes) -> rtc.AudioFrame:
    """Wrap WAV bytes into a single rtc.AudioFrame.

    Pure (no network / no dashscope), so it is unit-testable on its own. Derives
    `samples_per_channel` from the real PCM byte count rather than the WAV header,
    which the Qwen renderer fills with a bogus data-chunk size (same quirk that
    playback.wav_frames guards against).
    """
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav:
        sample_width = wav.getsampwidth()
        num_channels = wav.getnchannels()
        sample_rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())  # real data (bounded by file)
    samples_per_channel = len(frames) // (sample_width * num_channels)
    return rtc.AudioFrame(
        data=frames,
        sample_rate=sample_rate,
        num_channels=num_channels,
        samples_per_channel=samples_per_channel,
    )


def synthesize_clone(text: str, voice_id: str) -> rtc.AudioFrame:
    """Synthesize `text` in the enrolled clone `voice_id`; return one AudioFrame.

    BLOCKING (network) — call it off the event loop (e.g. asyncio.to_thread).
    Imports dashscope/httpx lazily so this module imports without them.
    """
    # Lazy import: dashscope/httpx are NOT in agent-py's base venv (see module
    # docstring). Keeping them inside the function lets `import agent` / the test
    # suite / ruff all run without them installed.
    import dashscope
    import httpx

    key = _api_key()
    dashscope.api_key = key
    dashscope.base_http_api_url = _BASE_HTTP_API_URL

    response = dashscope.MultiModalConversation.call(
        model=_TTS_MODEL,
        api_key=key,
        text=text,
        voice=voice_id,
        stream=False,
    )
    audio_url = response.output.audio.url
    wav_bytes = httpx.get(audio_url, timeout=30.0).content
    return wav_bytes_to_frame(wav_bytes)
