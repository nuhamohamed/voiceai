import asyncio
import logging
import pathlib
import sys
from collections.abc import AsyncIterable

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    ChatContext,
    ChatMessage,
    JobContext,
    JobProcess,
    ModelSettings,
    RunContext,
    StopResponse,
    TurnHandlingOptions,
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
from qwen_tts import synthesize_clone  # noqa: E402  clone-voice TTS for live answers
from standup_summary import (  # noqa: E402
    format_transcript,
    post_slack_summary,
    summarize_transcript,
)

logger = logging.getLogger("agent")

# LiveKit creds + Moss creds live in agent-py/.env.local; SLACK_WEBHOOK_URL (and
# other shared secrets) live in the repo-root .env. Load both — .env.local is
# loaded first so it wins for any overlapping key (load_dotenv won't override).
load_dotenv(".env.local")
load_dotenv(_REPO_ROOT / ".env")

PERSONA_ID = "person_a"  # the clone we demo

# Saying any of these ends the standup: the clone posts the Slack summary and
# leaves the room. Kept distinct from the demo-question keywords (block/status/
# auth/migration) so a wrap-up never collides with a scripted answer.
WRAP_UP_KEYWORDS = ("wrap up", "wrap-up", "adjourn", "end standup", "that's a wrap")


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
        self._voice_id = persona.voice_id  # enrolled Qwen clone, for live tts_node
        # Running transcript of the standup: (speaker, text) per turn. Filled by
        # record_turn() from the session's conversation_item_added event (wired
        # in my_agent). Used to build the end-of-standup Slack summary.
        self._transcript: list[tuple[str, str]] = []
        self._standup_ended = False  # guard: summarize + post at most once

    async def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        """Speak LIVE (off-script) answers in Person A's Qwen voice clone.

        The two scripted demo answers play pre-rendered WAVs via
        `session.say(..., audio=wav_frames(...))`, which BYPASSES the TTS step
        entirely — so this override never touches them and the scripted path is
        unchanged. It DOES handle every text-only utterance: off-script LLM
        replies plus the text-only `session.say()` greeting and wrap-up sign-off,
        which now also speak in the clone voice (consistent voice throughout).

        The pipeline still needs `tts=inference.TTS(...)` on the AgentSession (the
        default tts_node uses it); this override replaces the synthesis itself for
        the live path. We collect the (short, 1-3 sentence) text, synthesize once
        via Qwen, and yield a single 24kHz mono 16-bit AudioFrame.

        Synthesis is one-shot (non-streaming) and blocking, so we run it off the
        event loop with asyncio.to_thread; the live answer pauses briefly before
        speaking. On any failure we fall back to the default (generic-voice) TTS
        so the agent still answers rather than going silent.
        """
        collected = "".join([chunk async for chunk in text]).strip()
        if not collected:
            return
        try:
            frame = await asyncio.to_thread(synthesize_clone, collected, self._voice_id)
        except Exception:
            logger.exception(
                "Qwen clone TTS failed; falling back to default TTS for: %r",
                collected[:80],
            )

            async def _one() -> AsyncIterable[str]:
                yield collected

            async for f in Agent.default.tts_node(self, _one(), model_settings):
                yield f
            return
        yield frame

    def record_turn(self, speaker: str, text: str) -> None:
        """Append one conversation turn to the running standup transcript."""
        if text and text.strip():
            self._transcript.append((speaker, text))

    async def _end_standup(self) -> None:
        """Wrap up: build the transcript, summarize it, post to Slack, leave.

        Runs while the session is still alive, so `self.llm` is available and we
        are not bound by the 10s shutdown-hook timeout. Any failure in summarize
        or post is logged (inside post_slack_summary) but never blocks the agent
        from leaving the room.
        """
        if self._standup_ended:
            return
        self._standup_ended = True

        transcript = format_transcript(self._transcript)
        # @-mention the absent person this clone stood in for, so the summary
        # (posted to the single webhook channel) notifies the right teammate.
        mention = get_persona(self._persona_id).slack_user_id or None
        try:
            summary = await summarize_transcript(self.llm, transcript)
            await post_slack_summary(summary, mention_user_id=mention)
        except Exception:
            logger.exception("Failed to build/post the standup summary")

        # Leave the room (non-blocking; drains any pending speech first).
        self.session.shutdown(drain=True)

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

        # Wrap-up intent — ends the standup. Checked FIRST so "let's wrap up"
        # never falls into a demo-answer branch. We speak a short sign-off, then
        # summarize the transcript and post it to Slack before leaving.
        if any(k in q for k in WRAP_UP_KEYWORDS):
            await self.session.say(
                "Got it — that's a wrap. I'll post the standup summary to Slack "
                "and head out. Talk soon."
            )
            await self._end_standup()
            raise StopResponse()

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
        vad=ctx.proc.userdata["vad"],
        # Turn detection + preemptive generation now live under turn_handling
        # (the bare turn_detection=/preemptive_generation= kwargs are deprecated
        # for removal in v2.0). Behavior is preserved exactly:
        #   - turn_detection: the LiveKit multilingual turn detector (unchanged).
        #   - preemptive_generation {"enabled": False}: KEEP it OFF — a
        #     speculatively-started LLM reply could leak generic-voice audio
        #     before our on_user_turn_completed cached-WAV + StopResponse fires
        #     for the two demo questions. This is the equivalent of the old
        #     preemptive_generation=False.
        # See https://docs.livekit.io/reference/agents/turn-handling-options/
        turn_handling=TurnHandlingOptions(
            turn_detection=MultilingualModel(),
            preemptive_generation={"enabled": False},
        ),
    )

    assistant = Assistant(room=ctx.room)

    # Record every committed turn into the standup transcript. This fires for
    # user speech AND the agent's own replies — including the cached-WAV demo
    # answers, since session.say(..., add_to_chat_ctx=True) commits their text.
    # ConversationItemAddedEvent.item is a ChatMessage with .role/.text_content;
    # non-message items (tool calls) have no text and are skipped by record_turn.
    from livekit.agents import ConversationItemAddedEvent

    @session.on("conversation_item_added")
    def _on_item_added(ev: ConversationItemAddedEvent) -> None:
        item = ev.item
        if not isinstance(item, ChatMessage):
            return
        speaker = "Nuha (clone)" if item.role == "assistant" else "Teammate"
        assistant.record_turn(speaker, item.text_content or "")

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=assistant,
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
