"""End-of-standup summary: turn the meeting transcript into a Slack note.

This module is deliberately decoupled from LiveKit so each piece is unit-testable
without a live room, mic, or LiveKit credentials:

  - `format_transcript`   — pure: list of (speaker, text) turns -> one string.
  - `summarize_transcript` — one *silent* LLM call (no TTS); returns the note text.
  - `post_slack_summary`  — POST the note to an Incoming Webhook via httpx.

`agent.py` wires these together when the standup ends: it accumulates turns from
the `conversation_item_added` event, formats them, summarizes, and posts. The
agent then leaves the room. Keeping the LLM call and the HTTP POST here (behind
plain function signatures) means the demo-critical "did the note get built and
sent?" logic is covered by `tests/test_standup_summary.py` with mocks.
"""

from __future__ import annotations

import logging
import os

import httpx
from livekit.agents import ChatContext

logger = logging.getLogger("agent.standup_summary")

# --- The summary instruction (the main knob for WHAT the note contains) -------
# This is the highest-leverage decision in the feature: it defines what the
# absent person reads when they get back. Tune freely. It asks for the three
# things the user wants — what happened, what the clone surfaced/did, and what
# the person needs to follow up on — with concrete owners and deadlines.
SUMMARY_SYSTEM_PROMPT = (
    "You are the meeting notetaker for a standup that the user's AI clone "
    "attended on their behalf. From the transcript below, write a short Slack "
    "note addressed to the absent person (the one the clone stood in for). "
    "Use this exact structure with these headers:\n"
    "*Standup summary*\n"
    "- 2-4 bullets on what was discussed and decided.\n"
    "*What your clone covered*\n"
    "- 1-3 bullets on what the clone reported or answered on your behalf.\n"
    "*Action items*\n"
    "- One bullet per task as `owner - task (deadline)`; write `owner - task "
    "(no deadline)` when none was given.\n"
    "*For you to follow up on*\n"
    "- 1-3 bullets on anything that needs the absent person's attention.\n\n"
    "Rules: ground every line in the transcript — never invent owners, dates, "
    "or decisions. If a section has nothing, write `- (nothing)`. Keep it tight; "
    "this is a Slack message, not an essay. Use Slack mrkdwn (*bold*, `-` bullets)."
)


def format_transcript(turns: list[tuple[str, str]]) -> str:
    """Render accumulated (speaker, text) turns into a plain transcript string.

    Empty/whitespace-only turns are dropped so the LLM isn't fed blank lines
    (interim transcripts and tool items can produce empty text).
    """
    lines = [f"{speaker}: {text.strip()}" for speaker, text in turns if text.strip()]
    return "\n".join(lines)


async def summarize_transcript(
    summarizer,
    transcript: str,
    *,
    system_prompt: str = SUMMARY_SYSTEM_PROMPT,
) -> str:
    """Summarize the transcript with a single, silent (non-spoken) LLM call.

    `summarizer` is any LiveKit `llm.LLM` instance (we pass the agent's own
    configured LLM). We build a fresh `ChatContext` — system prompt + the
    transcript as one user message — and `collect()` the full response into a
    string. This never touches TTS, so nothing is spoken into the room.
    """
    if not transcript.strip():
        return "Standup summary: no conversation was captured."

    summary_ctx = ChatContext()
    summary_ctx.add_message(role="system", content=system_prompt)
    summary_ctx.add_message(
        role="user", content=f"Here is the standup transcript:\n\n{transcript}"
    )

    response = await summarizer.chat(chat_ctx=summary_ctx).collect()
    text = (response.text or "").strip()
    return text or "Standup summary: the summarizer returned no text."


async def post_slack_summary(summary: str, webhook_url: str | None = None) -> bool:
    """POST the summary to a Slack Incoming Webhook. Returns True on success.

    Reads `SLACK_WEBHOOK_URL` from the environment when `webhook_url` is omitted.
    Never raises into the caller: a missing URL or a failed POST is logged
    loudly (not swallowed silently) and reported via the return value, so the
    agent can still leave the room cleanly even if Slack delivery fails.
    """
    url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        logger.warning(
            "SLACK_WEBHOOK_URL is not set — skipping Slack summary post. "
            "Add it to agent-py/.env.local (or the repo-root .env)."
        )
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"text": summary})
    except httpx.HTTPError:
        logger.exception("Failed to POST standup summary to Slack")
        return False

    if resp.status_code != 200 or resp.text != "ok":
        # Slack webhooks return 200 + body "ok" on success; anything else is a
        # delivery failure (bad/expired webhook, malformed payload, etc.).
        logger.error(
            "Slack webhook rejected the summary: status=%s body=%s",
            resp.status_code,
            resp.text[:300],
        )
        return False

    logger.info("Posted standup summary to Slack (%d chars).", len(summary))
    return True
