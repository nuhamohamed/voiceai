"""Voice + STT config — produced by Nuha, consumed by Tony's LiveKit agent."""

STT_PLUGIN = "deepgram"       # LiveKit STT plugin to wire into the session
AUDIO_CACHE_DIR = "audio/demo"  # pre-rendered demo lines: {update,blocker,slack_summary}.wav
