"""Stage 2: pull Linear tickets for the absent teammate and emit JSONL records.

    # list candidate users so you can grab the right UUID for .env
    python scripts/pull_linear.py --list-users

    # pull tickets updated in the last 30 days for LINEAR_ABSENT_USER_ID
    # and append valid records to data/person_a_corpus.jsonl
    python scripts/pull_linear.py

Reads from .env (via python-dotenv if installed, else os.environ):
  LINEAR_API_KEY          — personal API key from Linear Settings → API
  LINEAR_ABSENT_USER_ID   — the Linear user UUID whose tickets we ingest

Emits records in the locked corpus shape (one JSON object per line):
  {"id": "lin-<identifier>", "source": "linear", "ref": "<identifier> <title>", "text": "..."}

Stdlib only. Source-driven: queries follow Linear's public GraphQL schema at
https://developers.linear.app/docs/graphql/working-with-the-graphql-api — if
the schema changes, update the query, don't guess fields.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

LINEAR_API = "https://api.linear.app/graphql"
CORPUS_PATH = Path("data/person_a_corpus.jsonl")
WINDOW_DAYS = 30

LIST_USERS_QUERY = """
query { users(first: 50) { nodes { id name email } } }
"""

# Pull issues assigned to a user updated within the window, with comments.
ISSUES_QUERY = """
query Issues($userId: ID!, $since: DateTimeOrDuration!) {
  issues(
    first: 50
    filter: {
      assignee: { id: { eq: $userId } }
      updatedAt: { gt: $since }
    }
  ) {
    nodes {
      identifier
      title
      description
      updatedAt
      state { name type }
      project { name }
      labels { nodes { name } }
      comments(first: 20) {
        nodes {
          body
          createdAt
          user { name }
        }
      }
    }
  }
}
"""


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore[import-not-found]
    except ImportError:
        return
    load_dotenv()


def _gql(query: str, variables: dict | None, api_key: str) -> dict:
    req = urllib.request.Request(
        LINEAR_API,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Linear API HTTP {e.code}: {e.read().decode(errors='replace')}")
    if "errors" in payload:
        sys.exit(f"Linear GraphQL errors: {payload['errors']}")
    return payload["data"]


def list_users(api_key: str) -> None:
    data = _gql(LIST_USERS_QUERY, None, api_key)
    print(f"{'id':<40}  name                 email")
    for u in data["users"]["nodes"]:
        print(f"{u['id']:<40}  {u['name']:<20} {u.get('email') or ''}")


def _issue_to_record(issue: dict) -> dict:
    ident = issue["identifier"]
    title = issue["title"] or ""
    desc = (issue.get("description") or "").strip()
    state = (issue.get("state") or {}).get("name", "Unknown")
    project = (issue.get("project") or {}).get("name") or "—"
    labels = [n["name"] for n in (issue.get("labels") or {}).get("nodes", [])]
    comments = (issue.get("comments") or {}).get("nodes", [])

    parts = [
        f"{title}",
        f"Status: {state}. Project: {project}." + (f" Labels: {', '.join(labels)}." if labels else ""),
    ]
    if desc:
        parts.append(f"Description: {desc}")
    if comments:
        parts.append("Comments:")
        for c in comments:
            who = (c.get("user") or {}).get("name", "?")
            when = (c.get("createdAt") or "")[:10]
            body = (c.get("body") or "").strip().replace("\n", " ")
            parts.append(f"  [{when}] {who}: {body}")

    return {
        "id": f"lin-{ident.lower()}",
        "source": "linear",
        "ref": f"{ident} {title}".strip(),
        "text": "\n".join(parts),
    }


def pull(api_key: str, user_id: str) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)).isoformat()
    data = _gql(ISSUES_QUERY, {"userId": user_id, "since": since}, api_key)
    issues = data["issues"]["nodes"]
    return [_issue_to_record(i) for i in issues]


def _existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids: set[str] = set()
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ids.add(json.loads(line)["id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return ids


def main() -> int:
    _load_dotenv()
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        sys.exit("LINEAR_API_KEY not set (copy .env.example to .env and fill it in)")

    if "--list-users" in sys.argv:
        list_users(api_key)
        return 0

    user_id = os.environ.get("LINEAR_ABSENT_USER_ID")
    if not user_id:
        sys.exit("LINEAR_ABSENT_USER_ID not set — run with --list-users to find the UUID")

    records = pull(api_key, user_id)
    print(f"Fetched {len(records)} ticket(s) updated in last {WINDOW_DAYS} days.")

    existing = _existing_ids(CORPUS_PATH)
    new_records = [r for r in records if r["id"] not in existing]
    skipped = len(records) - len(new_records)

    CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CORPUS_PATH.open("a") as f:
        for r in new_records:
            f.write(json.dumps(r) + "\n")

    print(f"Appended {len(new_records)} new record(s) to {CORPUS_PATH} (skipped {skipped} dup).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
