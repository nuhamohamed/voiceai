"""Validate the corpus file Melody hands off to Nuha.

    python scripts/seed_check.py [path]

Checks every line of `data/person_a_corpus.jsonl` (or the path you pass):
- parses as JSON
- has the required keys: id, source, ref, text
- source is one of: linear, slack, calendar
- text is non-empty
- ids are unique across the file

Prints per-source counts plus the first record as a sample, exits nonzero on
any failure so it's safe to chain in a script or pre-push hook.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ALLOWED_SOURCES = {"linear", "slack", "calendar"}
REQUIRED_KEYS = {"id", "source", "ref", "text"}
DEFAULT_PATH = "data/person_a_corpus.jsonl"


def check(path: Path) -> int:
    if not path.exists():
        print(f"FAIL: file not found: {path}", file=sys.stderr)
        return 1

    errors: list[str] = []
    ids_seen: set[str] = set()
    sources: Counter[str] = Counter()
    records: list[dict] = []

    with path.open() as f:
        for lineno, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError as e:
                errors.append(f"line {lineno}: JSON parse error — {e}")
                continue

            missing = REQUIRED_KEYS - rec.keys()
            if missing:
                errors.append(f"line {lineno}: missing keys {sorted(missing)}")
                continue

            if rec["source"] not in ALLOWED_SOURCES:
                errors.append(
                    f"line {lineno}: invalid source {rec['source']!r} "
                    f"(allowed: {sorted(ALLOWED_SOURCES)})"
                )
            if not str(rec["text"]).strip():
                errors.append(f"line {lineno}: empty text")
            if rec["id"] in ids_seen:
                errors.append(f"line {lineno}: duplicate id {rec['id']!r}")

            ids_seen.add(rec["id"])
            sources[rec["source"]] += 1
            records.append(rec)

    print(f"File:    {path}")
    print(f"Records: {len(records)}")
    for src, n in sorted(sources.items()):
        print(f"  {src:<10} {n}")

    if records:
        first = records[0]
        text = str(first["text"])
        preview = text[:120] + ("…" if len(text) > 120 else "")
        print("\nFirst record:")
        print(f"  id:     {first['id']}")
        print(f"  source: {first['source']}")
        print(f"  ref:    {first['ref']}")
        print(f"  text:   {preview}")

    if errors:
        print(f"\nFAIL — {len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print("\nOK — corpus valid.")
    return 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    sys.exit(check(Path(arg)))
