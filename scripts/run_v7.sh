#!/usr/bin/env bash
# v7 = v6 + CE+ (experiments/ceplus.py): budget-matched calibration (n_cal runs, as the baselines),
# deployment at the conformal quantile of a training-fixed dominating reference, and self-normalisation
# by the measured cross-track error of a headland probe line; PAC variant (delta = 0.1); new stack
# follow-previous-pass + Lenain (baseline with spec overlap and with CE+). Only the system-level
# comparison is rerun (the other experiments do not contain CE+).
#   JOBS=20 bash scripts/run_v7.sh
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS="${JOBS:-$(nproc)}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p results/logs
cd experiments
JOBFILE="../results/logs/jobs_v7.txt"
N=45
for ((i = 0; i < N; i++)); do
  echo python3 exp_system.py --fields 30 --tag _v7 --shard "$i" --nshards "$N" ">" "../results/logs/v7_system_${i}.log"
done > "$JOBFILE"
echo "$(wc -l < "$JOBFILE") v7 jobs, running $JOBS at a time"
xargs -P "$JOBS" -I{} bash -c "{} 2>&1" < "$JOBFILE"
echo "all v7 jobs finished"
