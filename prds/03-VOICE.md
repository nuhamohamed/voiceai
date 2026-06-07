# PRD 03 — Voice (Nuha)

**Owner:** Nuha · **Lane:** make the clone sound like Person A
**You hand off:** Person A's cloned voice + the speak/listen config → Tony.

## Your outcome

In the demo, the clone's update and answer **sound like Person A**, and a spoken question becomes text for the brain. The scripted "wow" lines play in A's cloned voice no matter what happens live.

## How cloning actually works here (verified — pick your path)

A Qwen-cloned voice does **not** drop straight into a LiveKit TTS slot. The real options:

- **Recommended (guaranteed + Qwen sponsor credit):** clone A **offline** with Qwen/Alibaba, **pre-render the scripted lines** as audio, play them in the room. Zero live risk, no paid plan needed.
- **Optional live clone:** LiveKit **Custom Voices** — clone in the LiveKit dashboard → `v_*` id → `tts="cartesia/sonic-3:v_…"`. ⚠️ needs a **paid LiveKit Cloud Ship-plan or higher** (uses Cartesia/Inworld, not Qwen) — confirm the hackathon plan tier first.
- **Unscripted live speech:** a stock plugin voice (MiniMax/OpenAI). *(The MiniMax LiveKit plugin can't clone — stock voices only.)*
- **STT:** a stock plugin (e.g. Deepgram) turns the spoken question into text.

The outcome (sounds like A, scripted lines guaranteed) is what matters — the mix is your call.

## Done looks like

- The scripted demo lines play in Person A's cloned voice (pre-rendered = always works).
- A spoken question is transcribed to text for the brain.
- Live answers speak in a voice (cloned if the plan allows, stock otherwise).

## Worth knowing

- The moat is live **retrieval**, not live **TTS** — cached cloned audio for the scripted lines is enough for the "wow." Don't over-invest in live cloning.
- Independent of Moss and the room — start anytime. Agree one thing with Tony: how he plugs your voice + STT into the session.

## Hand-off

Give Tony the voice + STT config and the cached audio files; he wires them in.
