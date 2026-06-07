"""Hardcoded demo personas (shared config). Tony owns the shape; Nuha fills voice_id.

A persona = a clone's identity: which Moss index to search, how it should sound/talk,
and the cloned-voice handle. Add/edit personas here; keep the dataclass shape stable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Persona:
    id: str  # namespace key, e.g. "person_a"
    name: str  # display name
    system_prompt: str  # character/voice + how to answer (grounding rules for the LLM)
    voice_id: str  # cloned-voice handle for TTS — filled by Nuha (Qwen / LiveKit Custom Voice)
    moss_index: str  # Moss index to retrieve from — usually == id
    slack_user_id: str = ""  # Slack member ID (e.g. "U01ABCDEF") — the absent
    # person the end-of-standup summary @-mentions in the summary channel. Find
    # it in Slack: click the person -> profile -> ... menu -> "Copy member ID".
    # Leave "" to post the summary without a mention.


_GROUNDING = (
    "You are {name}'s standup clone. Answer in first person, concisely, grounded ONLY "
    "in the retrieved context provided. If the context doesn't cover it, say you're not sure "
    "rather than guessing."
)

PERSONAS: dict[str, Persona] = {
    "person_a": Persona(
        id="person_a",
        name="Nuha",
        system_prompt=_GROUNDING.format(name="Nuha"),
        voice_id="qwen-tts-vc-nuha-voice-20260607144452804-6824",
        moss_index="person_a",
        slack_user_id="U0B8VKMQ4TC",  # Nuha — @-mentioned in the standup summary
    ),
    "person_b": Persona(
        id="person_b",
        name="Person B",
        system_prompt=_GROUNDING.format(name="Person B"),
        voice_id="qwen-tts-vc-nuha-voice-20260607144452804-6824",  # same clone for demo
        moss_index="person_b",
        slack_user_id="",  # TODO: set to Person B's Slack member ID (U...)
    ),
}


def get_persona(persona_id: str) -> Persona:
    if persona_id not in PERSONAS:
        raise KeyError(f"Unknown persona '{persona_id}'. Known: {list(PERSONAS)}")
    return PERSONAS[persona_id]
