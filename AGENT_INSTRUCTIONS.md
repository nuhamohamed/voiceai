# Agent Coordination Protocol

Every agent (A, B, C) must follow this protocol at the start and end of each work session, and periodically while working.

---

## 1. At Session Start — READ FIRST

Before writing any code, fetch and read the other agents' status files:

```
agent-status/agent-a.json
agent-status/agent-b.json
agent-status/agent-c.json
```

Check:
- **`files`** — are any files you plan to touch already claimed by another agent? If yes, stop and coordinate before proceeding.
- **`blockers`** — is any agent waiting on you? Resolve blockers before starting new work.
- **`status`** — is any agent in `review` state, meaning they may be pushing changes soon?

---

## 2. Claim Your Work — UPDATE YOUR STATUS FILE

Immediately update your own `agent-status/agent-X.json` with your current task and the files you will touch:

```json
{
  "agent": "A",
  "status": "working",
  "currentTask": "Implement login form validation",
  "files": ["src/auth/login.ts", "src/auth/validators.ts"],
  "blockers": [],
  "waitingOn": null,
  "lastUpdated": "2026-06-06T14:30:00Z",
  "notes": ""
}
```

Commit this immediately with the prefix `[status]`:

```
git add agent-status/agent-a.json
git commit -m "[status] Agent A: working on login validation"
git push
```

---

## 3. While Working — PERIODIC CHECK-INS

Every ~30 minutes (or after completing a sub-task), do two things:

**a) Pull and re-read the other agents' status files** to check for new file claims or blockers directed at you.

**b) Update your own status file** if your task or file list has changed, then commit and push with `[status]` prefix.

---

## 4. If You Need Another Agent — SET A BLOCKER

If your work is blocked waiting on another agent:

```json
{
  "status": "blocked",
  "blockers": ["Waiting on Agent B to finish the API endpoint in src/api/users.ts"],
  "waitingOn": "B"
}
```

Commit and push so the other agent sees it on their next check-in.

---

## 5. When Done — CLEAR YOUR STATUS

When your task is complete, push your code changes, then update your status:

```json
{
  "status": "idle",
  "currentTask": "",
  "files": [],
  "blockers": [],
  "waitingOn": null,
  "lastUpdated": "2026-06-06T16:00:00Z",
  "notes": "Login validation done, merged to main."
}
```

Commit with:
```
git commit -m "[status] Agent A: idle — login validation complete"
git push
```

---

## 6. File Conflict Rule

**You must not modify a file listed in another agent's `files` array without first:**
1. Checking if the other agent is actively editing it (status = `working`)
2. Coordinating via the `blockers` / `waitingOn` fields
3. Waiting until the other agent clears that file from their list

The dashboard at your GitHub Pages URL will show a red conflict warning automatically when two agents claim the same file.

---

## Status Values

| Value | Meaning |
|-------|---------|
| `idle` | No active work, safe to assign new tasks |
| `working` | Actively coding — files list is live |
| `blocked` | Waiting on another agent |
| `review` | Changes pushed, in PR/review — avoid the same files |

---

## Dashboard

View live status at your GitHub Pages URL (configured when you first open `docs/index.html`).

The dashboard auto-refreshes every 60 seconds and highlights file conflicts in red.
