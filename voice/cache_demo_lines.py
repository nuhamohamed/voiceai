"""
Pre-cache the exact demo lines as audio files.

Run this once before the demo so playback works even if live TTS fails.
Output goes to audio/demo/.

Usage:
  python -m voice.cache_demo_lines
"""

import pathlib

from voice.clone import load_voice_id, synthesize

DEMO_AUDIO_DIR = pathlib.Path("audio/demo")

# Edit these lines to match the exact demo script before the presentation
DEMO_LINES: dict[str, str] = {
    "update": (
        "Hey team, I'm double-booked right now so my clone is standing in for me. "
        "Here's my standup update: [FILL IN YOUR UPDATE HERE]."
    ),
    "question": (
        "[FILL IN THE EXACT QUESTION YOUR CLONE SHOULD ASK]"
    ),
    "report_back": (
        "Here's a summary of what happened: [FILL IN REPORT BACK HERE]."
    ),
}


def cache_all(voice_id: str) -> None:
    DEMO_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    for name, text in DEMO_LINES.items():
        out = str(DEMO_AUDIO_DIR / f"{name}.mp3")
        print(f"Caching '{name}' ...")
        synthesize(text, voice_id, out)
    print(f"\nAll demo lines cached to {DEMO_AUDIO_DIR}/")


if __name__ == "__main__":
    voice_id = load_voice_id()
    cache_all(voice_id)
