#!/usr/bin/env bash
# One-shot unattended run on a rented server: run everything, merge, build tables, push results.
# Usage (inside the cloned repo):  GH_TOKEN=<github token> nohup bash scripts/autorun.sh > autorun.log 2>&1 &
set -uo pipefail
cd "$(dirname "$0")/.."
pip install -q -r requirements.txt
bash scripts/run_all.sh
python3 scripts/merge_shards.py
python3 experiments/make_tables.py || true
git config user.name  "${GIT_NAME:-autorun}"
git config user.email "${GIT_EMAIL:-autorun@localhost}"
git add results
git commit -q -m "Experiment results from rented server ($(nproc) cores)" || true
for i in 1 2 3 4; do
  git pull -q --no-rebase "https://x-access-token:${GH_TOKEN}@github.com/michaeln2026j-ops/11111.git" claude/quirky-fermat-nr94ww \
    && git push -q "https://x-access-token:${GH_TOKEN}@github.com/michaeln2026j-ops/11111.git" HEAD:claude/quirky-fermat-nr94ww && break
  sleep $((2 ** i))
done
echo "AUTORUN DONE"
