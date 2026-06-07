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
    # Q1 answer — status question
    "update": (
        "The backend OAuth callback and token exchange shipped Tuesday — PR 847 merged "
        "and deployed to staging Wednesday, sign-in works there. Ivan reviewed the spec "
        "Wednesday and flagged that we need sliding-window refresh-token rotation with "
        "reuse detection before prod. I'm implementing that now under ENG-419 — should "
        "land Friday. Jamie's doing PKCE on the frontend in parallel under ENG-418. "
        "Earliest prod rollout: Tuesday next week."
    ),
    # Q2 answer — the moat moment
    "blocker": (
        "Ivan's concern is that the current implementation issues long-lived refresh "
        "tokens — if one leaks, the attacker has a long window. He wants each refresh "
        "to rotate the token and revoke the old one, with reuse detection that "
        "invalidates the whole token family if a stale refresh gets replayed. It's a "
        "bigger lift than I'd scoped, so I added it as ENG-419 and started Thursday. "
        "Should be done Friday for Ivan's review."
    ),
    # Slack summary posted after standup
    "slack_summary": (
        "Nuha's standup proxy summary — auth migration: backend shipped to staging "
        "Tuesday; blocked on refresh-token rotation ENG-419 for prod; targeting "
        "Tuesday June 9 rollout. Action: Nuha to finish ENG-419 for Ivan's review "
        "by Friday end of day. Frontend PKCE ENG-418, Jamie, in parallel."
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
