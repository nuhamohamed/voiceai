"""Mic-free proof of the end-of-standup Slack summary flow.

Three layers, none of which need a live room, mic, Slack, or an LLM:

  1. `format_transcript` — pure formatting; empty turns dropped.
  2. `summarize_transcript` — builds the right ChatContext and returns the LLM's
     text, via a fake LLM whose `.chat(chat_ctx=...).collect()` we control.
  3. `post_slack_summary` — posts `{"text": summary}` to the webhook (httpx
     mocked), and degrades gracefully (returns False, no raise) when the URL is
     missing or Slack rejects the payload.
  4. Routing — the REAL `Assistant.on_user_turn_completed` ends the standup on a
     wrap-up keyword: it raises StopResponse and triggers summarize + post,
     while leaving the two scripted demo questions untouched.

Style matches tests/test_demo_flow.py (path bootstrap, asyncio_mode=auto).
"""

from __future__ import annotations

import contextlib
import pathlib
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root
_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"  # agent-py/src
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import standup_summary as ss  # noqa: E402  module under test


# --- fakes ------------------------------------------------------------------
class _FakeStream:
    """Stands in for the LLMStream returned by llm.chat()."""

    def __init__(self, text: str) -> None:
        self._text = text

    async def collect(self):
        return SimpleNamespace(text=self._text, tool_calls=[], usage=None, extra={})


class _FakeLLM:
    """Records the ChatContext it was handed; returns a fixed completion."""

    def __init__(self, text: str) -> None:
        self._text = text
        self.last_ctx = None

    def chat(self, *, chat_ctx):
        self.last_ctx = chat_ctx
        return _FakeStream(self._text)


def _mock_httpx(post_mock: AsyncMock) -> MagicMock:
    """Build a replacement for httpx.AsyncClient supporting `async with`."""
    client = MagicMock()
    client.post = post_mock
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=cm)


# ---------------------------------------------------------------------------
# 1. format_transcript
# ---------------------------------------------------------------------------
def test_format_transcript_joins_and_drops_empty() -> None:
    turns = [
        ("Teammate", "what's the status?"),
        ("Nuha (clone)", "  PR #847 merged.  "),
        ("Teammate", "   "),  # whitespace-only -> dropped
        ("Nuha (clone)", ""),  # empty -> dropped
    ]
    out = ss.format_transcript(turns)
    assert out == "Teammate: what's the status?\nNuha (clone): PR #847 merged."


def test_format_transcript_empty_is_empty_string() -> None:
    assert ss.format_transcript([]) == ""


# ---------------------------------------------------------------------------
# 2. summarize_transcript
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_summarize_transcript_returns_llm_text_and_builds_context() -> None:
    fake = _FakeLLM("*Standup summary*\n- auth migration on track")
    transcript = "Teammate: status?\nNuha (clone): PR #847 merged."

    out = await ss.summarize_transcript(fake, transcript)

    assert out == "*Standup summary*\n- auth migration on track"
    # The context must carry the system prompt and the transcript verbatim.
    roles = [m.role for m in fake.last_ctx.items]
    assert roles == ["system", "user"]
    assert fake.last_ctx.items[0].text_content == ss.SUMMARY_SYSTEM_PROMPT
    assert transcript in fake.last_ctx.items[1].text_content


@pytest.mark.asyncio
async def test_summarize_transcript_empty_skips_llm() -> None:
    fake = _FakeLLM("should not be used")
    out = await ss.summarize_transcript(fake, "   ")
    assert "no conversation" in out.lower()
    assert fake.last_ctx is None  # LLM never called


# ---------------------------------------------------------------------------
# 3. post_slack_summary
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_post_slack_summary_posts_text_payload(monkeypatch) -> None:
    post = AsyncMock(return_value=SimpleNamespace(status_code=200, text="ok"))
    monkeypatch.setattr(ss.httpx, "AsyncClient", _mock_httpx(post))

    ok = await ss.post_slack_summary("the note", webhook_url="https://hooks/x")

    assert ok is True
    post.assert_awaited_once()
    args, kwargs = post.call_args
    assert args[0] == "https://hooks/x"
    assert kwargs["json"] == {"text": "the note"}


@pytest.mark.asyncio
async def test_post_slack_summary_prepends_mention(monkeypatch) -> None:
    post = AsyncMock(return_value=SimpleNamespace(status_code=200, text="ok"))
    monkeypatch.setattr(ss.httpx, "AsyncClient", _mock_httpx(post))

    ok = await ss.post_slack_summary(
        "the note", webhook_url="https://hooks/x", mention_user_id="U01ABC"
    )

    assert ok is True
    assert post.call_args.kwargs["json"] == {"text": "<@U01ABC>\nthe note"}


@pytest.mark.asyncio
async def test_post_slack_summary_missing_url_returns_false(monkeypatch) -> None:
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    post = AsyncMock()
    monkeypatch.setattr(ss.httpx, "AsyncClient", _mock_httpx(post))

    ok = await ss.post_slack_summary("the note")  # no url anywhere

    assert ok is False
    post.assert_not_awaited()  # never attempts the POST


@pytest.mark.asyncio
async def test_post_slack_summary_uses_env_when_url_omitted(monkeypatch) -> None:
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks/from-env")
    post = AsyncMock(return_value=SimpleNamespace(status_code=200, text="ok"))
    monkeypatch.setattr(ss.httpx, "AsyncClient", _mock_httpx(post))

    ok = await ss.post_slack_summary("the note")

    assert ok is True
    assert post.call_args.args[0] == "https://hooks/from-env"


@pytest.mark.asyncio
async def test_post_slack_summary_non_ok_returns_false(monkeypatch) -> None:
    post = AsyncMock(return_value=SimpleNamespace(status_code=404, text="no_service"))
    monkeypatch.setattr(ss.httpx, "AsyncClient", _mock_httpx(post))

    ok = await ss.post_slack_summary("the note", webhook_url="https://hooks/dead")

    assert ok is False


# ---------------------------------------------------------------------------
# 4. Routing — the real on_user_turn_completed ends the standup on wrap-up
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_wrap_up_keyword_ends_standup(monkeypatch) -> None:
    import personas
    from livekit.agents import AgentSession, ChatContext, ChatMessage, StopResponse

    import agent as agent_mod

    fake_summarize = AsyncMock(return_value="THE SUMMARY")
    fake_post = AsyncMock(return_value=True)
    monkeypatch.setattr(agent_mod, "summarize_transcript", fake_summarize)
    monkeypatch.setattr(agent_mod, "post_slack_summary", fake_post)
    # Give the demo persona a Slack ID so we can prove it flows to the mention.
    monkeypatch.setattr(personas.PERSONAS["person_a"], "slack_user_id", "U_TEST")

    async with AgentSession() as session:
        assistant = agent_mod.Assistant()  # room=None
        await session.start(assistant)
        assistant.session.say = AsyncMock()
        assistant.session.shutdown = MagicMock()  # non-blocking in prod; stub here

        # Pretend a couple of real turns were recorded before the wrap-up.
        assistant.record_turn("Teammate", "what's the status of auth?")
        assistant.record_turn("Nuha (clone)", "PR #847 merged to staging.")

        msg = ChatMessage(role="user", content=["ok everyone, let's wrap up"])
        stopped = False
        try:
            await assistant.on_user_turn_completed(ChatContext(), msg)
        except StopResponse:
            stopped = True

        assert stopped, "wrap-up must raise StopResponse (suppress the LLM)"
        fake_summarize.assert_awaited_once()
        # The transcript handed to the summarizer contains the recorded turns.
        transcript_arg = fake_summarize.await_args.args[1]
        assert "PR #847 merged" in transcript_arg
        fake_post.assert_awaited_once_with("THE SUMMARY", mention_user_id="U_TEST")
        assistant.session.shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_wrap_up_only_summarizes_once(monkeypatch) -> None:
    from livekit.agents import AgentSession, ChatContext, ChatMessage, StopResponse

    import agent as agent_mod

    fake_post = AsyncMock(return_value=True)
    monkeypatch.setattr(agent_mod, "summarize_transcript", AsyncMock(return_value="S"))
    monkeypatch.setattr(agent_mod, "post_slack_summary", fake_post)

    async with AgentSession() as session:
        assistant = agent_mod.Assistant()
        await session.start(assistant)
        assistant.session.say = AsyncMock()
        assistant.session.shutdown = MagicMock()

        for _ in range(2):  # a second wrap-up must not double-post
            with contextlib.suppress(StopResponse):
                await assistant.on_user_turn_completed(
                    ChatContext(), ChatMessage(role="user", content=["let's wrap up"])
                )

        fake_post.assert_awaited_once()  # guarded by _standup_ended
