#!/usr/bin/env bash
# GitHub-driven remote agent: lets the analysis session operate this server without SSH.
#
#  * every POLL seconds: git pull the work branch; every new file control/queue/<id>.sh is
#    executed once (in the background, from the repo root) with output in control/out/<id>.log
#  * outputs (control/out/*, results/*.csv, results/tables.md, a heartbeat) are pushed to the
#    separate branch "server-out" so the pull request stays clean
#
# Start once (inside the cloned repo; the clone URL already carries the token):
#   nohup bash scripts/remote_agent.sh > remote_agent.log 2>&1 &
# Stop:  kill $(cat ~/.remote_agent.pid)
# This file is never modified after being pushed.
set -u
cd "$(dirname "$0")/.."
REPO="$(pwd)"
BR="${BR:-claude/quirky-fermat-nr94ww}"
OUT_BR="${OUT_BR:-server-out}"
POLL="${POLL:-60}"
REMOTE="$(git remote get-url origin)"
STATE="$HOME/.remote_agent_done"
OUTDIR="$HOME/server-out"
mkdir -p "$HOME"
echo $$ > "$HOME/.remote_agent.pid"
touch "$STATE" || { echo "cannot write state file $STATE"; exit 1; }
mkdir -p control/out control/queue

git config user.name "remote-agent"
git config user.email "remote-agent@localhost"
# flaky links to GitHub (e.g. from mainland China): HTTP/1.1, abort stalled transfers, retry next loop
git config http.version HTTP/1.1
git config http.lowSpeedLimit 1000
git config http.lowSpeedTime 60

pull_main() {  # network failure -> skip this round; merge conflict -> abort merge; never reset local work
  timeout 180 git fetch -q origin "$BR" >/dev/null 2>&1 || return 1
  git merge -q --no-edit FETCH_HEAD >/dev/null 2>&1 || { git merge --abort >/dev/null 2>&1; return 1; }
}

# output worktree on an orphan branch (created on first use)
if [ ! -d "$OUTDIR/.git" ]; then
  rm -rf "$OUTDIR"; mkdir -p "$OUTDIR"
  ( cd "$OUTDIR" && git init -q && git remote add origin "$REMOTE" \
    && git config user.name "remote-agent" && git config user.email "remote-agent@localhost" \
    && git config http.version HTTP/1.1 \
    && { git fetch -q origin "$OUT_BR" 2>/dev/null && git checkout -q -B "$OUT_BR" FETCH_HEAD \
         || git checkout -q --orphan "$OUT_BR"; } )
  git -C "$OUTDIR" config http.version HTTP/1.1
fi

push_outputs() {
  mkdir -p "$OUTDIR/out" "$OUTDIR/results"
  cp -f control/out/* "$OUTDIR/out/" 2>/dev/null
  cp -f results/*.csv results/tables.md "$OUTDIR/results/" 2>/dev/null
  mkdir -p "$OUTDIR/logs" && cp -f results/logs/*.log "$OUTDIR/logs/" 2>/dev/null
  ( cd "$OUTDIR" && git add -A . >/dev/null 2>&1 \
    && { git diff --cached --quiet || git commit -q -m "server outputs $(date -u +%m-%dT%H:%M)"; } \
    && timeout 180 git push -q origin "HEAD:$OUT_BR" >/dev/null 2>&1 )
}

while true; do
  pull_main
  for f in control/queue/*.sh; do
    [ -f "$f" ] || continue
    id="$(basename "$f" .sh)"
    grep -qx "$id" "$STATE" 2>/dev/null && continue
    echo "$id" >> "$STATE" || continue           # never run a command we cannot record
    grep -qx "$id" "$STATE" 2>/dev/null || continue
    echo "[$(date -u +%H:%M:%S)] start $id" >> control/out/agent.log
    ( cd "$REPO" && nohup bash "$f" > "control/out/$id.log" 2>&1; echo "[exit $?] $(date -u +%H:%M:%S)" >> "control/out/$id.log" ) &
  done
  {
    echo "time_utc $(date -u +%Y-%m-%dT%H:%M:%S)"; echo "nproc $(nproc)"; uptime
    free -g 2>/dev/null | head -2; df -h . 2>/dev/null | tail -1
    echo "commit $(git rev-parse --short HEAD)"; echo "--- processes"
    ps -eo pid,etimes,pcpu,args --sort=-pcpu | grep -E "python3|bash (control|scripts)" | grep -v grep | head -40
  } > control/out/heartbeat.txt 2>&1
  push_outputs
  sleep "$POLL"
done
