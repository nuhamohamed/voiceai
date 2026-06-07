"""Turn a persona's source documents (PDF / DOCX / images) into corpus chunks via Unsiloed.

This is a PRE-PARSE step — run it ONCE per document set, before the demo:

    python -m brain.ingest_docs person_a data/docs/auth-migration-rfc.pdf

It writes ``data/<persona>_docs.jsonl`` in the SAME shared contract as the
hand-authored corpus — ``{"id","source","ref","text"}`` — so ``brain/ingest.py``
merges it into the persona's Moss index alongside ``<persona>_corpus.jsonl``.
The live demo path therefore stays Moss-only: Unsiloed runs here, at ingest
time, and never in the hot path.

Why Unsiloed: its Parse endpoint already chunks. Each returned chunk carries an
``embed`` field — "combined Markdown content from all segments in the chunk,
ready for embedding into a vector store" — which is exactly our ``text``. The
segments carry ``page_number`` and ``segment_type`` for building a human ``ref``.

API contract (grounded, not from memory):
  POST https://prod.visionapi.unsiloed.ai/parse        multipart: file=<binary>
       header: api-key: <UNSILOED_API_KEY>           -> {"job_id", "status"}
  GET  https://prod.visionapi.unsiloed.ai/parse/{job_id}
       header: api-key: <UNSILOED_API_KEY>           -> {"status": "Succeeded",
                                                          "chunks": [{embed, segments:[...]}]}
  Sources:
    https://docs.unsiloed.ai/api-reference/parser/parse-document
    https://docs.unsiloed.ai/document-processing/parsing/response-format

Env vars required (from .env):
    UNSILOED_API_KEY — from the Unsiloed dashboard
"""
from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"

PARSE_URL = "https://prod.visionapi.unsiloed.ai/parse"
POLL_INTERVAL_S = 5.0
POLL_TIMEOUT_S = 300.0

# Parse options (sent as multipart form fields alongside the file).
# Source: https://docs.unsiloed.ai/api-reference/parser/parse-document
#   force_ocr   — read the rendered page image, NOT the PDF's embedded text
#                 layer. Tool-generated PDFs (like this one) often emit text in
#                 a broken order that interleaves bold runs; force_ocr bypasses
#                 that and reads in true visual order, fixing reading order while
#                 keeping tables clean via the vision model.
#   advanced    — higher-quality agentic OCR.
PARSE_OPTIONS = {
    "ocr_strategy": "force_ocr",
    "agentic_ocr": "advanced",
}

# Segment types that are page furniture, not content — never worth a corpus chunk.
# Source (segment_type enum): https://docs.unsiloed.ai/document-processing/parsing/element-types
_FURNITURE = {"PageHeader", "PageFooter"}
_HEADING = {"SectionHeader", "Title"}


async def parse_document(path: pathlib.Path, api_key: str, client: httpx.AsyncClient) -> dict:
    """Submit one document to Unsiloed Parse and poll until it succeeds.

    Returns the final job payload (which includes ``chunks``). Raises on failure
    or timeout. Source: docs.unsiloed.ai/api-reference/parser/parse-document
    """
    headers = {"api-key": api_key}

    with open(path, "rb") as fh:
        files = {"file": (path.name, fh, "application/pdf")}
        resp = await client.post(PARSE_URL, headers=headers, files=files, data=PARSE_OPTIONS)
    resp.raise_for_status()
    job_id = resp.json()["job_id"]
    print(f"  [{path.name}] submitted — job_id={job_id}; polling ...")

    status_url = f"{PARSE_URL}/{job_id}"
    waited = 0.0
    while waited < POLL_TIMEOUT_S:
        await asyncio.sleep(POLL_INTERVAL_S)
        waited += POLL_INTERVAL_S
        poll = await client.get(status_url, headers=headers)
        poll.raise_for_status()
        data = poll.json()
        status = data.get("status")
        if status == "Succeeded":
            print(f"  [{path.name}] parsed — {data.get('total_chunks', '?')} chunks.")
            return data
        if status == "Failed":
            raise RuntimeError(f"Unsiloed parse failed: {data.get('message', 'unknown error')}")

    raise TimeoutError(f"Unsiloed parse timed out after {POLL_TIMEOUT_S:.0f}s for {path.name}")


# ──────────────────────────────────────────────────────────────────────────────
# THE SHAPING DECISION — how a parsed chunk becomes a corpus record.
#
# This is the one judgment call that's visible in the demo: `ref` is what the
# on-screen retrieval trace shows during a live follow-up (brain/retrieval.py
# surfaces source + ref). The default below builds "<file> p.<page> — <heading>".
# Tweak this function to change how document citations read on screen.
# ──────────────────────────────────────────────────────────────────────────────
def chunk_to_record(chunk: dict, doc_name: str, idx: int) -> dict | None:
    """Map one Unsiloed chunk -> a corpus record, or None to drop it.

    text:  chunk["embed"] (combined Markdown for the whole chunk).
    ref:   "<doc_name> p.<page> — <nearest heading>", for the on-screen trace.
    source:"doc" — a new source type alongside linear | slack | calendar.
    """
    segments = chunk.get("segments") or []
    content_segs = [s for s in segments if s.get("segment_type") not in _FURNITURE]
    if not content_segs:
        return None

    text = (chunk.get("embed") or "").strip()
    if not text:
        # Fallback if a chunk lacks the combined `embed`: join segment markdown.
        text = "\n\n".join((s.get("markdown") or s.get("content") or "").strip()
                           for s in content_segs).strip()
    if not text:
        return None

    page = next((s.get("page_number") for s in content_segs
                 if s.get("page_number") is not None), None)
    heading = next((s.get("content", "").strip() for s in content_segs
                    if s.get("segment_type") in _HEADING and s.get("content")), "")

    ref = doc_name
    if page is not None:
        ref += f" p.{page}"
    if heading:
        ref += f" — {heading}"

    return {
        # Stable, positional id — NOT Unsiloed's per-parse chunk_id (a fresh UUID
        # every parse), so re-parsing the same doc upserts in place instead of
        # leaving orphaned stale chunks in the index.
        "id": f"doc-{pathlib.Path(doc_name).stem}-{idx}",
        "source": "doc",
        "ref": ref,
        "text": text,
    }


async def ingest_docs(persona_id: str, doc_paths: list[pathlib.Path]) -> None:
    api_key = os.getenv("UNSILOED_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Set UNSILOED_API_KEY in .env first (from the Unsiloed dashboard)."
        )

    records: list[dict] = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for path in doc_paths:
            if not path.exists():
                raise FileNotFoundError(path)
            result = await parse_document(path, api_key, client)
            for idx, chunk in enumerate(result.get("chunks") or []):
                rec = chunk_to_record(chunk, path.name, idx)
                if rec is not None:
                    records.append(rec)

    out = DATA_DIR / f"{persona_id}_docs.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\nWrote {len(records)} document chunks -> {out}")
    print("Now run `python -m brain.ingest` to load them into Moss.")


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: python -m brain.ingest_docs <persona_id> <doc.pdf> [doc2.pdf ...]")
        raise SystemExit(2)
    persona_id = sys.argv[1]
    doc_paths = [pathlib.Path(p) for p in sys.argv[2:]]
    asyncio.run(ingest_docs(persona_id, doc_paths))


if __name__ == "__main__":
    main()
