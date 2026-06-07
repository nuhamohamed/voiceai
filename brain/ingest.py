"""Load each persona's corpus into Moss.

Run once before the demo (or whenever the corpus changes):
    python -m brain.ingest

Creates one Moss index per persona (index_name == persona_id).
source + ref are stored as metadata so retrieve() can surface them in the trace.

Env vars required:
    MOSS_PROJECT_ID   — from portal.usemoss.dev
    MOSS_PROJECT_KEY  — from portal.usemoss.dev
"""
from __future__ import annotations

import asyncio
import json
import os
import pathlib

from dotenv import load_dotenv
from moss import DocumentInfo, MossClient, MutationOptions

load_dotenv()

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"

# Personas to ingest — index_name == persona_id
PERSONAS = ["person_a", "person_b"]


def _load_corpus(persona_id: str) -> list[DocumentInfo]:
    path = DATA_DIR / f"{persona_id}_corpus.jsonl"
    if not path.exists():
        fallback = DATA_DIR / "sample_corpus.jsonl"
        print(f"  [{persona_id}] corpus not found, using sample: {fallback}")
        path = fallback

    docs: list[DocumentInfo] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            docs.append(
                DocumentInfo(
                    id=row["id"],
                    text=row["text"],
                    metadata={
                        "source": row.get("source", ""),
                        "ref": row.get("ref", ""),
                    },
                )
            )
    return docs


async def ingest(persona_id: str, client: MossClient) -> None:
    docs = _load_corpus(persona_id)
    print(f"[{persona_id}] Ingesting {len(docs)} documents into Moss index '{persona_id}' ...")

    # Check if index already exists; upsert if so, create fresh if not.
    existing = await client.list_indexes()
    existing_names = {idx.name for idx in (existing or [])}

    if persona_id in existing_names:
        print(f"  [{persona_id}] Index exists — upserting documents.")
        await client.add_docs(persona_id, docs, MutationOptions(upsert=True))
    else:
        print(f"  [{persona_id}] Creating new index.")
        await client.create_index(persona_id, docs)

    # Preload so first retrieve() call is instant.
    await client.load_index(persona_id)
    print(f"  [{persona_id}] Done — index loaded and ready.\n")


async def main() -> None:
    project_id = os.getenv("MOSS_PROJECT_ID")
    project_key = os.getenv("MOSS_PROJECT_KEY")
    if not project_id or not project_key:
        raise EnvironmentError(
            "Set MOSS_PROJECT_ID and MOSS_PROJECT_KEY in .env first.\n"
            "Get them from https://portal.usemoss.dev"
        )

    client = MossClient(project_id, project_key)
    for persona_id in PERSONAS:
        await ingest(persona_id, client)

    print("All personas ingested. Run `python -m brain.retrieval_test` to verify.")


if __name__ == "__main__":
    asyncio.run(main())
