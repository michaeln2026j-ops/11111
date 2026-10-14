#!/usr/bin/env bash
# v8 confirmatory run (docs/theory_v8.md): CE+ with training-only gating (Proposition B), on FRESH
# fields (offset 50: fields 50-79 of each kind, never used by v1-v7). Primary method and claims are
# pre-registered in docs/theory_v8.md section 3, committed before this run.
#   JOBS=20 bash scripts/run_v8.sh
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS="${JOBS:-$(nproc)}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p results/logs
cd experiments
JOBFILE="../results/logs/jobs_v8.txt"
N=45
for ((i = 0; i < N; i++)); do
  echo python3 exp_system.py --fields 30 --tag _v8 --offset 50 --shard "$i" --nshards "$N" ">" "../results/logs/v8_system_${i}.log"
done > "$JOBFILE"
echo "$(wc -l < "$JOBFILE") v8 jobs, running $JOBS at a time"
xargs -P "$JOBS" -I{} bash -c "{} 2>&1" < "$JOBFILE"
echo "all v8 jobs finished"
