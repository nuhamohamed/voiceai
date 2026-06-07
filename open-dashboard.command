#!/bin/bash
# Double-click this to open the Standup Proxy dashboard.
# It serves from the repo root (so the local agent-status/*.json load) and opens your browser.
# Close this window (or Ctrl-C) to stop the server.
cd "$(dirname "$0")" || exit 1
PORT=8000

# Refresh the activity feed from git now, and every 15s while running.
# (fetch is read-only — it won't touch your working tree.)
refresh() { git fetch -q origin 2>/dev/null; python3 scripts/gen_activity.py >/dev/null 2>&1; }
refresh
( while true; do sleep 15; refresh; done ) &
LOOP_PID=$!
trap "kill $LOOP_PID 2>/dev/null" EXIT

( sleep 1; open "http://localhost:$PORT/docs/" 2>/dev/null ) &

echo "Standup Proxy dashboard  ->  http://localhost:$PORT/docs/"
echo "(activity feed refreshes from git every 15s; close this window to stop)"
python3 -m http.server "$PORT"
