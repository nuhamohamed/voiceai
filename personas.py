"""Hardcoded demo personas (shared config). Tony owns the shape; Nuha fills voice_id.

A persona = a clone's identity: which Moss index to search, how it should sound/talk,
and the cloned-voice handle. Add/edit personas here; keep the dataclass shape stable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Persona:
    id: str            # namespace key, e.g. "person_a"
    name: str          # display name
    system_prompt: str # character/voice + how to answer (grounding rules for the LLM)
    voice_id: str      # cloned-voice handle for TTS — filled by Nuha (Qwen / LiveKit Custom Voice)
    moss_index: str    # Moss index to retrieve from — usually == id


_GROUNDING = (
    "You are {name}'s standup clone. Answer in first person, concisely, grounded ONLY "
    "in the retrieved context provided. If the context doesn't cover it, say you're not sure "
    "rather than guessing."
)

PERSONAS: dict[str, Persona] = {
    "person_a": Persona(
        id="person_a",
        name="Person A",
        system_prompt=_GROUNDING.format(name="Person A"),
        voice_id="",          # TODO(Nuha): cloned-voice handle
        moss_index="person_a",
    ),
    "person_b": Persona(
        id="person_b",
        name="Person B",
        system_prompt=_GROUNDING.format(name="Person B"),
        voice_id="",          # TODO(Nuha)
        moss_index="person_b",
    ),
}


def get_persona(persona_id: str) -> Persona:
    if persona_id not in PERSONAS:
        raise KeyError(f"Unknown persona '{persona_id}'. Known: {list(PERSONAS)}")
    return PERSONAS[persona_id]
