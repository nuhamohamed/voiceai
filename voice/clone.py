"""
Voice cloning and TTS using Qwen (DashScope).

Usage:
  python -m voice.clone enroll voice_samples/nuha.m4a
  python -m voice.clone speak "Hello world" <voice_id> audio/test.mp3
"""

import base64
import json
import os
import pathlib
import sys

import httpx
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")
ENROLLMENT_URL = "https://dashscope-intl.aliyuncs.com/api/v1/services/audio/tts/customization"
TTS_MODEL = "qwen3-tts-vc-2026-01-22"
VOICE_ID_PATH = pathlib.Path("voice_samples/voice_id.json")


def enroll_voice(audio_path: str, name: str = "nuha") -> str:
    """Upload audio sample to Qwen, return the cloned voice_id."""
    audio_bytes = pathlib.Path(audio_path).read_bytes()
    # m4a is MPEG-4 audio
    suffix = pathlib.Path(audio_path).suffix.lower()
    mime = "audio/mp4" if suffix == ".m4a" else f"audio/{suffix.lstrip('.')}"
    data_uri = f"data:{mime};base64,{base64.b64encode(audio_bytes).decode()}"

    payload = {
        "model": "qwen-voice-enrollment",
        "input": {
            "action": "create",
            "target_model": TTS_MODEL,
            "preferred_name": name,
            "audio": {"data": data_uri},
        },
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    print(f"Enrolling voice from {audio_path} ...")
    resp = httpx.post(ENROLLMENT_URL, json=payload, headers=headers)
    resp.raise_for_status()
    voice_id = resp.json()["output"]["voice"]
    print(f"Voice enrolled: {voice_id}")

    # Persist so other scripts can reuse without re-enrolling
    VOICE_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
    VOICE_ID_PATH.write_text(json.dumps({"voice_id": voice_id, "name": name}))
    print(f"Saved voice_id to {VOICE_ID_PATH}")
    return voice_id


def synthesize(text: str, voice_id: str, output_path: str) -> None:
    """Synthesize text in the cloned voice and save to output_path."""
    dashscope.api_key = API_KEY
    dashscope.base_websocket_api_url = (
        "wss://dashscope-intl.aliyuncs.com/api-ws/v1/inference"
    )

    synthesizer = SpeechSynthesizer(model=TTS_MODEL, voice=voice_id)
    audio = synthesizer.call(text)

    out = pathlib.Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio)
    print(f"Saved audio: {output_path}")


def load_voice_id() -> str:
    """Load the persisted voice_id, raise if not enrolled yet."""
    if not VOICE_ID_PATH.exists():
        raise FileNotFoundError(
            f"No voice_id found at {VOICE_ID_PATH}. Run enrollment first:\n"
            "  python -m voice.clone enroll voice_samples/nuha.m4a"
        )
    return json.loads(VOICE_ID_PATH.read_text())["voice_id"]


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "enroll":
        audio = sys.argv[2] if len(sys.argv) > 2 else "voice_samples/nuha.m4a"
        enroll_voice(audio)

    elif cmd == "speak":
        text = sys.argv[2]
        voice_id = sys.argv[3] if len(sys.argv) > 3 else load_voice_id()
        out = sys.argv[4] if len(sys.argv) > 4 else "audio/test.mp3"
        synthesize(text, voice_id, out)

    else:
        print(__doc__)
