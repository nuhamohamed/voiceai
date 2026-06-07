import logging
import pathlib
import sys

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    ChatContext,
    ChatMessage,
    JobContext,
    JobProcess,
    RunContext,
    StopResponse,
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

    async def on_user_turn_completed(
        self, turn_ctx: ChatContext, new_message: ChatMessage
    ) -> None:
        """Question-triggered cached clone-voice answers for the two demo questions.

        The demo is QUESTION-TRIGGERED (not an unprompted monologue): the PM asks
        Q1 (status) then Q2 (blocker). For each, we run the REAL retrieve() so the
        on-screen Moss trace reflects exactly what Moss returns, then speak the
        pre-rendered clone-voice WAV (the transcript text matches demo-script.md so
        the on-screen transcript lines up), and raise StopResponse so the LLM does
        not also answer. Any other question falls through to the normal LLM
        search_knowledge path.
        """
        q = (new_message.text_content or "").lower()

        # Blocker intent (Q2 — the moat). Check first: "what's blocking it" must
        # not be swallowed by the status branch.
        if any(k in q for k in ("block", "blocking", "blocker")):
            chunks = await retrieve(new_message.text_content, self._persona_id)
            await self._publish_moss_context(new_message.text_content, chunks)
            wav = str(_REPO_ROOT / AUDIO_CACHE_DIR / "blocker.wav")
            await self.session.say(
                "Ivan's concern is that the current implementation issues "
                "long-lived refresh tokens — if one leaks, the attacker has a long "
                "window. He wants each refresh to rotate the token and revoke the "
                "old one, with reuse detection that invalidates the whole token "
                "family if a stale refresh gets replayed. It's a bigger lift than "
                "I'd scoped, so I added it as ENG-419 and started Thursday. Should "
                "be done Friday for Ivan's review.",
                audio=wav_frames(wav),
            )
            raise StopResponse()

        # Status intent (Q1 — opening). e.g. "what's the status of the auth
        # migration?" / "where is the migration?" — status/update/where + the topic.
        if any(k in q for k in ("status", "update", "where")) and any(
            k in q for k in ("auth", "migration")
        ):
            chunks = await retrieve(new_message.text_content, self._persona_id)
            await self._publish_moss_context(new_message.text_content, chunks)
            wav = str(_REPO_ROOT / AUDIO_CACHE_DIR / "update.wav")
            await self.session.say(
                "The backend OAuth callback and token exchange shipped Tuesday — "
                "PR #847 merged and deployed to staging Wednesday, sign-in works "
                "there. Ivan reviewed the spec Wednesday and flagged that we need "
                "sliding-window refresh-token rotation with reuse detection before "
                "prod. I'm implementing that now under ENG-419 — should land Friday. "
                "Jamie's doing PKCE on the frontend in parallel under ENG-418. "
                "Earliest prod rollout: Tuesday next week.",
                audio=wav_frames(wav),
            )
            raise StopResponse()

        # Otherwise: fall through to the normal LLM + search_knowledge path.

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
        # Keep preemptive generation OFF: a speculatively-started LLM reply could
        # leak generic-voice audio before our on_user_turn_completed cached-WAV +
        # StopResponse fires for the two demo questions.
        # See https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=False,
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

    # Short spoken greeting once connected. The demo OPENS with the PM asking Q1,
    # so the clone must NOT monologue update.wav unprompted — that line is now
    # triggered by the status question in on_user_turn_completed. Triggered here
    # (not in Agent.on_enter) per the documented LiveKit pattern so it runs
    # against a connected room and on_enter stays deterministic for the test suite.
    await session.say("Hi, I'm Nuha's standup clone — ask me anything about my work.")


if __name__ == "__main__":
    cli.run_app(server)
