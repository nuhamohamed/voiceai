# voiceai — Agent Coordination Rules

This project has three agents working in parallel: Agent A, Agent B, and Agent C.
Each agent owns one status file. Read this entire file before doing anything.

---

## Step 1 — Identify yourself

Determine which agent you are based on who is running you:
- Collaborator 1 → **Agent A**
- Collaborator 2 → **Agent B**
- Collaborator 3 (Nuha) → **Agent C**

---

## Step 2 — Read the other agents' status (BEFORE writing any code)

Fetch and read the two status files that are NOT yours:

| Agent | Status file |
|-------|-------------|
| A | `agent-status/agent-a.json` |
| B | `agent-status/agent-b.json` |
| C | `agent-status/agent-c.json` |

Raw URLs (always fetch fresh):
- https://raw.githubusercontent.com/nuhamohamed/voiceai/main/agent-status/agent-a.json
- https://raw.githubusercontent.com/nuhamohamed/voiceai/main/agent-status/agent-b.json
- https://raw.githubusercontent.com/nuhamohamed/voiceai/main/agent-status/agent-c.json

Check:
- **`files`** — do not touch any file listed in another agent's `files` array without coordinating first
- **`blockers`** — if another agent is waiting on you, address it before starting new work
- **`status`** — if another agent is `working` or `review`, be extra cautious about shared files

---

## Step 3 — Claim your work before writing any code

Update your own status file immediately:

```json
{
  "agent": "A",
  "status": "working",
  "currentTask": "short description of what you are doing",
  "files": ["list/of/every/file.ts", "you/plan/to/touch.ts"],
  "blockers": [],
  "waitingOn": null,
  "lastUpdated": "ISO timestamp",
  "notes": ""
}
```

Then commit and push:
```bash
git add agent-status/agent-X.json
git commit -m "[status] Agent X: <what you're doing>"
git push
```

---

## Step 4 — Check in every 30 minutes while working

```bash
git pull origin main
```

Then re-read the other agents' JSON files. If your task or file list changed, update your own JSON and push again.

---

## Step 5 — Clear your status when done

```bash
# update your agent-X.json: set status "idle", clear files and currentTask
git add agent-status/agent-X.json
git commit -m "[status] Agent X: idle — <what you finished>"
git push
```

Always `git pull` before starting the next task.

---

## Rules

- **You may only write to your own status file.** Never edit another agent's JSON.
- **Never touch a file in another agent's `files` list** without first coordinating via the `blockers` / `waitingOn` fields.
- **Always `git pull` before starting new work** to avoid overwriting changes.
- **Use `[status]` prefix on all status commits** so they are easy to identify in the dashboard.

---

## Status values

| Value | Meaning |
|-------|---------|
| `idle` | No active work — safe to assign tasks |
| `working` | Actively coding — files list is live |
| `blocked` | Waiting on another agent |
| `review` | Changes pushed, in PR — avoid same files |

---

## Dashboard

Human-readable view of all agent statuses and recent commits:
https://nuhamohamed.github.io/voiceai/
