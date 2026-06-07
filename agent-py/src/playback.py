"""Stream a local WAV file into the room as AudioFrames (LiveKit Playing Audio recipe).

IMPORTANT: our Qwen-rendered WAVs have a BOGUS data-chunk size in the header —
`wave.getnframes()` reports ~1.07e9 frames for a ~30s clip (verified). The
recipe's `samples_per_channel=wav.getnframes()` would feed that garbage to
AudioFrame and break playback. So derive samples_per_channel from the bytes
actually read. `readframes` is bounded by the real file data, so it returns the
true ~30s of audio.
"""
from __future__ import annotations

import wave
from collections.abc import AsyncIterator

from livekit import rtc


async def wav_frames(path: str) -> AsyncIterator[rtc.AudioFrame]:
    with wave.open(path, "rb") as wav:
        sample_width = wav.getsampwidth()
        num_channels = wav.getnchannels()
        frames = wav.readframes(wav.getnframes())                       # real data (bounded by file)
        samples_per_channel = len(frames) // (sample_width * num_channels)  # robust to bogus header
        yield rtc.AudioFrame(
            data=frames,
            sample_rate=wav.getframerate(),
            num_channels=num_channels,
            samples_per_channel=samples_per_channel,
        )
