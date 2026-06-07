# Live Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fork the `moss-hacker-starter` into `feat/tony-live-agent` and adapt it so Person A's clone joins a LiveKit room, gives the standup update, and answers a live follow-up grounded in our corpus via `retrieve()`, with the retrieved source shown on screen.

**Architecture:** Reuse the starter's LiveKit agent (`agent-py/`) + Next.js trace panel (`frontend/`). Rewire its `search_knowledge` tool to call our `retrieve()` seam (ignore the starter's own Moss code), point it at the `person_a` corpus + persona, play the cached clone-voice WAV as the opening update, and emit the trace in the exact `moss_context` shape the frontend already parses (so the panel needs ~no changes). Voice clone on the answer is a final swap.

**Tech Stack:** Python 3.10+ (uv), LiveKit Agents (`AgentServer`, Inference STT=deepgram/LLM/TTS), Next.js + pnpm frontend, our stdlib `brain.retrieval` seam.

**Source of truth:** `prds/04-LIVE-AGENT-DESIGN.md`. Ground every LiveKit change in the LiveKit Docs MCP — do not invent API.

---

## File structure

| File | Responsibility |
|---|---|
| `agent-py/` (from starter) | the LiveKit voice agent (uv project, own `.env.local`) |
| `agent-py/src/agent.py` (modify) | agent: persona, `search_knowledge → retrieve()`, opening update, drop memory tools |
| `agent-py/src/grounding.py` (create) | pure adapters: chunks → LLM text, chunks → `moss_context` payload |
| `agent-py/src/playback.py` (create) | `wav_frames(path)` → async `rtc.AudioFrame` generator |
| `agent-py/tests/test_grounding.py` (create) | unit tests for the pure adapters |
| `frontend/` (from starter) | Next.js trace panel (pnpm), consumes `moss_context` packets |
| `.gitignore` (modify) | append starter ignores (`node_modules/`, `.venv/`, `.next/`) |
| `package.json` (create, from starter) | root orchestrator (`pnpm dev` runs agent + frontend) |

**Consumed, never edited:** `brain/retrieval.py` (`retrieve`, `RetrievedChunk`), `personas.py` (`get_persona`), `voice/config.py`, `audio/demo/*.wav`, `data/person_a_corpus.jsonl`.

---

## Task 0: Pull the starter and verify it boots

**Files:**
- Create: `agent-py/`, `frontend/`, `package.json` (copied from starter)
- Modify: `.gitignore`

- [ ] **Step 1: Clone the starter to a temp dir**

Run:
```bash
git clone --depth 1 https://github.com/livekit-examples/moss-hacker-starter /tmp/moss-starter
```
Expected: clone succeeds; `/tmp/moss-starter/agent-py` and `/tmp/moss-starter/frontend` exist.

- [ ] **Step 2: Copy the two apps + orchestrator into the repo (do NOT overwrite our README/LICENSE/.gitignore)**

Run:
```bash
cp -R /tmp/moss-starter/agent-py /tmp/moss-starter/frontend ./
cp /tmp/moss-starter/package.json ./package.json
```
Expected: `agent-py/`, `frontend/`, `package.json` now in repo root. `git status` shows them untracked; our `README.md`/`LICENSE`/`.gitignore` unchanged.

- [ ] **Step 3: Append starter ignores to our `.gitignore`**

Append these lines to `.gitignore`:
```
# moss-hacker-starter apps
node_modules/
agent-py/.venv/
frontend/.next/
frontend/out/
agent-py/.ruff_cache/
agent-py/.pytest_cache/
**/__pycache__/
.env.local
.env.*.local
```

- [ ] **Step 4: Put LiveKit creds into the agent + frontend env files**

We already have LiveKit creds in the repo-root `.env`. Copy the three values into both app env files (these `.env.local` files are gitignored):
```bash
cp agent-py/.env.example agent-py/.env.local
cp frontend/.env.example frontend/.env.local
```
Then add to **`agent-py/.env.local`** and **`frontend/.env.local`** the three lines (copy the values from the repo-root `.env`):
```
LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```
Frontend also needs `AGENT_NAME=agent-py` (already set by the starter's example).

- [ ] **Step 5: Install deps**

Run:
```bash
uv --directory agent-py sync
uv --directory agent-py run python -m livekit.agents download-files
```
Expected: venv created; VAD/turn-detector model files downloaded.

- [ ] **Step 6: Smoke test the unmodified agent in console mode**

Run:
```bash
uv --directory agent-py run src/agent.py console
```
Expected: agent boots, greets as the "LiveKit docs helper". (Moss search will error without Moss creds — that's fine; we replace it in Task 2.) Type a sentence, confirm STT→LLM→TTS round-trips. Ctrl-C to exit.

- [ ] **Step 7: Commit**

```bash
git add agent-py frontend package.json .gitignore
git commit -m "chore(agent): vendor moss-hacker-starter (agent-py + frontend)"
```

---

## Task 1: Pure grounding adapters (TDD)

These map our `RetrievedChunk` to (a) the LLM grounding text and (b) the exact `moss_context` payload the frontend already parses. Pure functions, fully unit-tested.

**Files:**
- Create: `agent-py/src/grounding.py`
- Test: `agent-py/tests/test_grounding.py`

- [ ] **Step 1: Write the failing tests**

Create `agent-py/tests/test_grounding.py`:
```python
import sys, pathlib
_ROOT = pathlib.Path(__file__).resolve().parents[2]            # repo root: brain.retrieval, personas, voice
_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"    # agent-py/src: grounding, playback
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from brain.retrieval import RetrievedChunk
from grounding import format_chunks_for_llm, build_moss_context_payload


def _chunks():
    return [
        RetrievedChunk(text="Auth migration blocked on ENG-419.", source="linear", ref="ENG-412", score=0.91),
        RetrievedChunk(text="Ivan wants refresh-token rotation.", source="slack", ref="#security", score=0.74),
    ]


def test_format_chunks_for_llm_joins_ref_and_text():
    out = format_chunks_for_llm(_chunks())
    assert "ENG-412" in out and "Auth migration blocked" in out
    assert "#security" in out


def test_format_chunks_for_llm_empty_is_honest():
    assert "No relevant" in format_chunks_for_llm([])


def test_build_payload_matches_frontend_contract():
    p = build_moss_context_payload("why is auth blocked?", _chunks())
    assert p["type"] == "moss_context"
    d = p["data"]
    assert d["query"] == "why is auth blocked?"
    assert isinstance(d["matches"], list) and len(d["matches"]) == 2
    m0 = d["matches"][0]
    assert m0["text"] == "Auth migration blocked on ENG-419."
    assert m0["score"] == 0.91
    assert m0["metadata"]["ref"] == "ENG-412"
    assert m0["metadata"]["source"] == "linear"
    assert isinstance(d["timestamp"], (int, float))  # epoch seconds
```

- [ ] **Step 2: Run the tests, verify they fail**

Run: `uv --directory agent-py run pytest tests/test_grounding.py -v`
Expected: FAIL — `ModuleNotFoundError: src.grounding`.

- [ ] **Step 3: Implement `grounding.py`**

Create `agent-py/src/grounding.py`:
```python
"""Pure adapters: our RetrievedChunk -> LLM grounding text + the frontend's moss_context payload.

Keeping these pure (no I/O) makes them unit-testable and keeps agent.py thin.
The moss_context shape MUST match frontend/hooks/useMossContextEvents.ts: a
data.matches list of {text, score?, metadata?}. We put ref/source in metadata so
the on-screen panel can show "ENG-412 (linear)".
"""
from __future__ import annotations

from datetime import datetime, timezone


def format_chunks_for_llm(chunks) -> str:
    """One grounded block per chunk, labelled by ref so the LLM can cite it."""
    parts = [f"[{c.ref}] {c.text}".strip() for c in chunks if getattr(c, "text", "").strip()]
    return "\n\n".join(parts) if parts else "No relevant context was found for that question."


def build_moss_context_payload(query: str, chunks) -> dict:
    """Shape the trace exactly as the frontend panel expects."""
    matches = []
    for c in chunks:
        entry = {"text": (c.text or "").strip(), "score": float(c.score)}
        entry["metadata"] = {"ref": c.ref, "source": c.source}
        matches.append(entry)
    return {
        "type": "moss_context",
        "data": {
            "query": query,
            "matches": matches,
            "timestamp": datetime.now(timezone.utc).timestamp(),  # epoch seconds; frontend *1000
        },
    }
```

- [ ] **Step 4: Run the tests, verify they pass**

Run: `uv --directory agent-py run pytest tests/test_grounding.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add agent-py/src/grounding.py agent-py/tests/test_grounding.py
git commit -m "feat(agent): grounding adapters (chunks -> LLM text + moss_context payload)"
```

---

## Task 2: Rewire the agent to our retrieve() + persona, drop memory

Replace the starter's Moss-backed docs-helper with our standup clone: persona from `get_persona`, `search_knowledge → retrieve()`, the `moss_context` packet fed our chunks, memory tools removed.

**Files:**
- Modify: `agent-py/src/agent.py`

- [ ] **Step 1: Add the repo-root import bridge + our imports**

In `agent-py/src/agent.py`, after the existing imports, add:
```python
import sys, pathlib
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]   # agent-py/src/agent.py -> repo root
_SRC = pathlib.Path(__file__).resolve().parents[0]         # agent-py/src
for _p in (str(_REPO_ROOT), str(_SRC)):                    # explicit inserts: robust across dev/start
    if _p not in sys.path:                                 # subprocess spawn (don't rely on sys.path[0])
        sys.path.insert(0, _p)

from brain.retrieval import retrieve            # noqa: E402  our seam (Nuha's Moss lands behind it)
from personas import get_persona                # noqa: E402
from grounding import format_chunks_for_llm, build_moss_context_payload  # noqa: E402
```
(We insert `src/` explicitly rather than trusting `sys.path[0]`, because LiveKit `dev`/`start` spawn job subprocesses where the script-dir-on-path assumption may not hold.)
Remove the starter's `from moss import DocumentInfo, MossClient, QueryOptions` line.

- [ ] **Step 2: Set the demo persona constant**

Replace the `KNOWLEDGE_INDEX`/`MEMORY_INDEX`/`DEFAULT_USER_ID` block with:
```python
PERSONA_ID = "person_a"  # the clone we demo
```

- [ ] **Step 3: Rewrite the `Assistant` class — persona instructions, one tool, no Moss client**

Replace the entire `Assistant` class with:
```python
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
        chunks = await retrieve(query, self._persona_id)   # our seam; Moss behind it
        await self._publish_moss_context(query, chunks)    # drives the on-screen panel
        return format_chunks_for_llm(chunks)
```
(This deletes `remember_fact`, `recall_facts`, the `MossClient`, and the `on_enter` Moss-load.)

- [ ] **Step 4: Update the entrypoint — drop user_id/metadata, pass room only**

In `my_agent`, remove the `user_id`/`ctx.job.metadata` parsing block, and change the agent start to:
```python
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
    await ctx.connect()
```
Leave the greeting `generate_reply(...)` for now (Task 3 replaces it with the cached update).

- [ ] **Step 5: Run tests + lint**

Run:
```bash
uv --directory agent-py run pytest -q
uv --directory agent-py run ruff check src/
```
Expected: grounding tests pass; ruff clean (fix any unused-import from the removed Moss line).

- [ ] **Step 6: Console smoke test against our corpus (stub retrieve, no Moss creds needed)**

Run: `uv --directory agent-py run src/agent.py console`
Then type: `what is blocking the auth migration?`
Expected: the agent calls `search_knowledge`, the answer is grounded in our corpus (mentions ENG-419 / refresh-token rotation / Ivan), spoken via TTS. (The stub `retrieve()` reads `data/person_a_corpus.jsonl`.)

- [ ] **Step 7: Commit**

```bash
git add agent-py/src/agent.py
git commit -m "feat(agent): standup clone — search_knowledge calls our retrieve(), drop memory tools"
```

---

## Task 3: Opening standup update from the cached clone WAV

On join, the clone delivers the update in its cloned voice by playing `audio/demo/update.wav`.

**Files:**
- Create: `agent-py/src/playback.py`
- Modify: `agent-py/src/agent.py`

- [ ] **Step 1: Create the WAV → AudioFrame helper (verified against the Playing Audio recipe)**

Create `agent-py/src/playback.py`:
```python
"""Stream a local WAV file into the room as AudioFrames (LiveKit Playing Audio recipe).

IMPORTANT: our Qwen-rendered WAVs have a BOGUS data-chunk size in the header —
`wave.getnframes()` reports ~1.07e9 frames for a ~30s clip (verified). The
recipe's `samples_per_channel=wav.getnframes()` would feed that garbage to
AudioFrame and break playback. So derive samples_per_channel from the bytes
actually read. `readframes` is bounded by the real file data, so it returns the
true ~30s of audio.
"""
from __future__ import annotations

import wave
from collections.abc import AsyncIterator

from livekit import rtc


async def wav_frames(path: str) -> AsyncIterator[rtc.AudioFrame]:
    with wave.open(path, "rb") as wav:
        sample_width = wav.getsampwidth()
        num_channels = wav.getnchannels()
        frames = wav.readframes(wav.getnframes())                       # real data (bounded by file)
        samples_per_channel = len(frames) // (sample_width * num_channels)  # robust to bogus header
        yield rtc.AudioFrame(
            data=frames,
            sample_rate=wav.getframerate(),
            num_channels=num_channels,
            samples_per_channel=samples_per_channel,
        )
```

- [ ] **Step 2: Read the cache dir from voice.config + resolve the update path**

In `agent-py/src/agent.py` import block (after the bridge), add:
```python
from voice.config import AUDIO_CACHE_DIR        # noqa: E402  Nuha's seam
from playback import wav_frames                  # noqa: E402  flat import (src/ on sys.path[0])
```

- [ ] **Step 3: Replace the greeting with the cached update**

In `my_agent`, replace the final `await session.generate_reply(instructions=...)` greeting with:
```python
    update_wav = str(_REPO_ROOT / AUDIO_CACHE_DIR / "update.wav")
    update_text = (
        "Here's my standup update."  # transcript shown on screen; audio is the clone voice
    )
    await session.say(update_text, audio=wav_frames(update_wav))
```

- [ ] **Step 4: Console smoke test the opening update**

Run: `uv --directory agent-py run src/agent.py console`
Expected: on connect, the clone plays `update.wav` (the cached standup update in the cloned voice), then waits for a question. Ask the auth-migration question → grounded answer (generic TTS for now).

- [ ] **Step 5: Commit**

```bash
git add agent-py/src/playback.py agent-py/src/agent.py
git commit -m "feat(agent): play cached clone-voice update.wav on join"
```

---

## Task 4: Frontend trace panel shows OUR chunks

Task 1 emits the exact `moss_context` shape the **parser** (`useMossContextEvents.ts`) expects, so the hook needs no change. But the **panel** (`moss-results-panel.tsx`) only renders `text` + `score` by default — it ignores `metadata`. So this task wires creds, runs it, rebrands, and adds a few lines to surface our `ref`/`source` badge. (The chunk *text* already shows ENG-419 etc., so the moat lands either way; the badge is the polish.)

**Files:**
- Modify: `frontend/app-config.ts` (branding), `frontend/components/app/moss-results-panel.tsx` (heading + render metadata)

- [ ] **Step 1: Install frontend deps**

Run: `pnpm --dir frontend install`
Expected: install completes (Node 22+, pnpm 10+).

- [ ] **Step 2: Run agent + frontend together**

Run: `pnpm dev`
Open `http://localhost:3000`, click **Start call**, allow mic.
Expected: the clone plays the update; ask "what's blocking the auth migration?"; the **panel fills with our chunk(s)** — the retrieved text + relevance score — as the clone answers. (The `ref`/`source` badge appears after Step 3.)

- [ ] **Step 3: Rebrand + surface the ref/source badge (keep TypeScript strict)**

**a.** In `frontend/app-config.ts`, set branding to the Standup Proxy (e.g. `companyName: "Standup Proxy"`, page title "Person A — Standup Clone").

**b.** In `frontend/components/app/moss-results-panel.tsx`, change the heading `Knowledge Matches` → `🔎 Moss source`.

**c.** In the same file, render our `metadata.ref`/`metadata.source` above each chunk. Replace the `matches.map(...)` block with:
```tsx
{matches.map((match, index) => {
  const meta = (match.metadata ?? {}) as { ref?: string; source?: string };
  return (
    <li key={`${id}-${index}`} className="space-y-1">
      {meta.ref && (
        <p className="text-foreground text-xs font-semibold">
          🔎 {meta.ref}{meta.source ? ` (${meta.source})` : ''}
        </p>
      )}
      <p className="leading-snug">{match.text}</p>
      {typeof match.score === 'number' && (
        <p className="text-muted-foreground text-xs">Relevance: {match.score.toFixed(2)}</p>
      )}
    </li>
  );
})}
```
Do not loosen `tsconfig` strictness; the `meta` cast narrows the parser's `unknown` metadata to a typed shape.

- [ ] **Step 4: Lint the frontend (project rule: run after changes)**

Run: `pnpm --dir frontend lint`
Expected: no errors (TypeScript strict stays on).

- [ ] **Step 5: Commit**

```bash
git add frontend/app-config.ts frontend/components/app/moss-results-panel.tsx
git commit -m "feat(frontend): rebrand panel to Standup Proxy / Moss source"
```

---

## Task 5: End-to-end live demo (generic voice) — the recordable moat

- [ ] **Step 1: Full run**

Run: `pnpm dev` → `http://localhost:3000` → Start call.
Walk the script: clone plays the update → ask the rehearsed follow-up (*"What exactly is Ivan's concern and when does it hit prod?"*) → confirm: (a) the 🔎 panel shows the real `ENG-419`/Ivan chunk, (b) the spoken answer is grounded in it, (c) it happens live.

- [ ] **Step 2: Verify the moat criteria (LIV-01..03)**

Confirm: room + turn-taking ✅; clone gives the update ✅; live question → `retrieve()` → visible panel → grounded spoken answer ✅. Note: voice is still generic here — Task 6 makes the answer clone-voiced.

- [ ] **Step 3: Commit a checkpoint tag**

```bash
git commit --allow-empty -m "chore: LIV-01..03 working end-to-end (generic voice)"
```

---

## Task 6: Clone voice on the answer (decision task)

The starter answers in generic `inference.TTS`. Pick ONE path to put the answer in the clone voice. **6a is the default** (assets already exist, sponsor-aligned Qwen, recorded video = known question). 6b is the cleanest if an ElevenLabs key is available.

### Option 6a — Play the cached clone WAV for the scripted answer (default)

**Files:** Modify: `agent-py/src/agent.py`

> **Spike first (5 min):** `session.say(audio=…)` + `StopResponse()` inside `on_user_turn_completed` is the one unproven mechanism in this plan. Prove it in isolation before relying on it. If it fights you, the fallback is clean — Task 5's generic answer + the clone-voice *opening update* already demonstrate the clone, so ship that.

- [ ] **Step 1: Disable preemptive generation (so it can't race the cached WAV)**

The starter sets `preemptive_generation=True`, which starts the LLM reply *before* the turn ends — it could leak a half-generated generic-voice answer before our `StopResponse()` fires. In `my_agent`'s `AgentSession(...)`, set:
```python
        preemptive_generation=False,
```

- [ ] **Step 2: Route the rehearsed follow-up to `blocker.wav`, suppress the LLM's spoken reply**

Add an `on_user_turn_completed` hook to `Assistant` that, for the demo question, retrieves (drives the panel) and speaks the cached clone WAV instead of an LLM-generated answer:
```python
from livekit.agents import ChatContext, ChatMessage, StopResponse  # add to imports

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        q = (new_message.text_content or "").lower()
        if any(k in q for k in ("ivan", "blocker", "rotation", "blocking", "prod")):
            chunks = await retrieve(new_message.text_content, self._persona_id)
            await self._publish_moss_context(new_message.text_content, chunks)  # real trace on screen
            wav = str(_REPO_ROOT / AUDIO_CACHE_DIR / "blocker.wav")
            await self.session.say(
                "Ivan flagged refresh-token rotation; tracking it as ENG-419.",  # transcript
                audio=wav_frames(wav),  # cloned-voice audio
            )
            raise StopResponse()  # don't let the LLM also answer
```

- [ ] **Step 3: Console + frontend verification**

Run: `pnpm dev`, ask the blocker question. Expected: panel shows the real chunk AND the answer is spoken in the **clone voice** (the cached WAV). Other questions still go through the live LLM path (generic voice).

- [ ] **Step 4: Commit**

```bash
git add agent-py/src/agent.py
git commit -m "feat(agent): clone-voice answer for the scripted blocker question (cached WAV)"
```

### Option 6b — ElevenLabs clone plugin (all answers live + clone, needs key)

**Files:** Modify: `agent-py/src/agent.py`, `agent-py/.env.local`

- [ ] **Step 1:** `uv --directory agent-py add "livekit-agents[elevenlabs]~=1.5"`
- [ ] **Step 2:** Add `ELEVEN_API_KEY=...` to `agent-py/.env.local` and clone the persona's voice in ElevenLabs to get a `voice_id`.
- [ ] **Step 3:** In `my_agent`, swap the TTS line:
```python
from livekit.plugins import elevenlabs  # add to imports
# ...
        tts=elevenlabs.TTS(voice_id="<cloned-voice-id>", model="eleven_turbo_v2_5"),
```
- [ ] **Step 4:** `pnpm dev`, verify every answer streams in the clone voice with the panel.
- [ ] **Step 5:** Commit: `git commit -am "feat(agent): clone voice via ElevenLabs plugin"`

---

## Task 7: Record + open PR

- [ ] **Step 1:** Update `agent-status/agent-tony.json` → status `review`, note "live agent works LIV-01..03 + clone voice".
- [ ] **Step 2:** Record the 2-minute demo video (update → follow-up → panel + grounded clone-voice answer).
- [ ] **Step 3:** Push the branch and open a PR to `main`:
```bash
git push -u origin feat/tony-live-agent
gh pr create --base main --title "Live agent (PRD-04): standup clone + Moss trace panel" --body "Forks moss-hacker-starter; search_knowledge -> retrieve(); cached clone-voice update + answer; on-screen Moss source panel. LIV-01..03. Slack (LIV-04) deferred."
```

---

## Coordination notes (not edits)

- **Nuha:** the agent calls `retrieve()`; her real Moss lands behind it with no agent change. Heads-up that the starter's own Moss code is intentionally unused (we use her seam).
- **Open voice decision:** 6a (cached Qwen WAV — default) vs 6b (ElevenLabs). Pick at Task 6 based on whether an ElevenLabs key is available; 6a needs nothing new.
- **Deferred:** Slack summary (LIV-04) — a webhook POST of `slack_summary.wav`'s text on adjourn; add after the moat is recorded.
