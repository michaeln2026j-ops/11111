#!/usr/bin/env bash
# Install deps now, wait until experiments/.system_ready is pushed (all baselines and the
# real-GNSS error model validated), then run the FULL suite once, merge, build tables, push.
# Usage (inside the cloned repo):
#   GH_TOKEN=<token> nohup bash scripts/autorun2.sh > autorun2.log 2>&1 &
# Optional faster pip mirror:  PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
# This file is never modified after being pushed (it git-pulls while running).
set -uo pipefail
cd "$(dirname "$0")/.."
REMOTE="https://x-access-token:${GH_TOKEN}@github.com/michaeln2026j-ops/11111.git"
BR=claude/quirky-fermat-nr94ww
pip install -q ${PIP_INDEX_URL:+-i "$PIP_INDEX_URL"} numpy scipy pandas shapely scikit-learn matplotlib
python3 -c "import numpy, scipy, pandas, shapely, sklearn, matplotlib; print('deps ready')"
echo "waiting for experiments/.system_ready  $(date)"
for t in $(seq 1 288); do  # up to 24 h, poll every 5 min
  git pull -q --no-rebase "$REMOTE" "$BR" || true
  [ -f experiments/.system_ready ] && break
  sleep 300
done
echo "marker found, running full suite on $(nproc) cores  $(date)"
bash scripts/run_all.sh
python3 scripts/merge_shards.py
python3 experiments/make_tables.py || true
git config user.name "autorun"
git config user.email "autorun@localhost"
git add results
git commit -q -m "Full experiment results from rented server ($(nproc) cores)" || true
for i in 1 2 3 4 5; do
  git pull -q --no-rebase "$REMOTE" "$BR" && git push -q "$REMOTE" "HEAD:$BR" && break
  sleep $((2 ** i))
done
echo "AUTORUN2 DONE $(date)"
