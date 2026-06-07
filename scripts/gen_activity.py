"""Generate docs/activity.json from git history — the changelog the dashboard shows.

Cards show CURRENT status (the JSON overwrites each update); this feed keeps the FULL
history, because git never forgets. Prefers origin/main (the team's pushed commits) so
you see everyone's activity, falling back to local HEAD.

Run by open-dashboard.command, or manually:  python3 scripts/gen_activity.py
"""
import json
import os
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
OUT = os.path.join(ROOT, "docs", "activity.json")
SEP = "\x1f"  # unit separator — safe field delimiter


def _has_ref(ref: str) -> bool:
    return subprocess.run(
        ["git", "-C", ROOT, "rev-parse", "--verify", "--quiet", ref],
        capture_output=True, text=True,
    ).returncode == 0


def main() -> None:
    ref = "origin/main" if _has_ref("origin/main") else "HEAD"
    fmt = SEP.join(["%h", "%an", "%ar", "%s"])  # sha, author, relative date, subject
    log = subprocess.run(
        ["git", "-C", ROOT, "log", ref, "-n", "60", f"--pretty=format:{fmt}"],
        capture_output=True, text=True,
    ).stdout
    rows = []
    for line in log.splitlines():
        parts = line.split(SEP)
        if len(parts) == 4:
            sha, author, date, subject = parts
            rows.append({"sha": sha, "author": author, "date": date, "subject": subject})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print(f"wrote {len(rows)} commits from {ref} -> {OUT}")


if __name__ == "__main__":
    main()
