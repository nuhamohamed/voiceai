import logging
import pathlib
import sys

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    inference,
    room_io,
)
from livekit.plugins import ai_coustics, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

_REPO_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
)  # agent-py/src/agent.py -> repo root
_SRC = pathlib.Path(__file__).resolve().parents[0]  # agent-py/src
for _p in (str(_REPO_ROOT), str(_SRC)):  # explicit inserts: robust across dev/start
    if _p not in sys.path:  # subprocess spawn (don't rely on sys.path[0])
        sys.path.insert(0, _p)

from brain.retrieval import retrieve  # noqa: E402  our seam (Nuha's Moss behind it)
from personas import get_persona  # noqa: E402
from voice.config import AUDIO_CACHE_DIR  # noqa: E402  Nuha's seam

from grounding import build_moss_context_payload, format_chunks_for_llm  # noqa: E402
from playback import wav_frames  # noqa: E402  flat import (src/ on sys.path[0])

logger = logging.getLogger("agent")

load_dotenv(".env.local")

PERSONA_ID = "person_a"  # the clone we demo


class Assistant(Agent):
    """Person A's standup clone: answers follow-ups grounded in retrieve() context."""

    def __init__(self, *, room=None) -> None:
        persona = get_persona(PERSONA_ID)
        super().__init__(
            llm=inference.LLM(model="openai/gpt-5.2-chat-latest"),
            instructions=(
                persona.system_prompt
                + "\n\nFor ANY question about this person's work, ALWAYS call "
                "search_knowledge FIRST and ground your reply only in the returned "
                "context. Keep replies to one to three plain-text sentences for voice. "
                "If the context doesn't cover it, say you're not sure rather than guessing."
            ),
        )
        self._room = room
        self._persona_id = PERSONA_ID

    async def _publish_moss_context(self, query: str, chunks) -> None:
        if self._room is None:
            return
        import json

        try:
            payload = build_moss_context_payload(query, chunks)
            await self._room.local_participant.publish_data(
                payload=json.dumps(payload, default=str).encode("utf-8"), reliable=True
            )
        except Exception:
            logger.exception("Failed to publish moss_context data")

    @function_tool()
    async def search_knowledge(self, context: RunContext, query: str) -> str:
        """Search this person's real work context (Linear / Slack / calendar) to ground your answer.

        Call this before answering any question about their work, status, blockers, or tickets.

        Args:
            query: The user's question or topic to look up.
        """
        chunks = await retrieve(query, self._persona_id)  # our seam; Moss behind it
        await self._publish_moss_context(query, chunks)  # drives the on-screen panel
        return format_chunks_for_llm(chunks)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


# Keep the registered dispatch name as "agent-py": the frontend (Task 6) sets
# AGENT_NAME=agent-py to dispatch explicitly to this worker. Do not rename.
@server.rtc_session(agent_name="agent-py")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using LiveKit Inference and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=inference.STT(model="deepgram/nova-3", language="multi"),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(room=ctx.room),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_S
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    # Deliver the standup update once connected. Triggered here (not in
    # Agent.on_enter) per the documented LiveKit pattern so it runs against a
    # connected room and on_enter stays deterministic for the test suite. We
    # play the cached clone-voice WAV instead of a generated greeting so the
    # opening update lands in the person's actual voice.
    update_wav = str(_REPO_ROOT / AUDIO_CACHE_DIR / "update.wav")
    update_text = (
        "Here's my standup update."  # transcript shown on screen; audio is the clone voice
    )
    await session.say(update_text, audio=wav_frames(update_wav))


if __name__ == "__main__":
    cli.run_app(server)
