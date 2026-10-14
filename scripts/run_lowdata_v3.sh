#!/usr/bin/env bash
# E-low v3 (docs/prereg_lowdata_v3.md): test fields 5-19 per regime: phase A (theory CDF, oracle), then the
# lambda curves. Resumable (finished fields / curves are skipped).   JOBS=2 bash scripts/run_lowdata_v3.sh
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS="${JOBS:-$(nproc)}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p results/logs results/lowdata_v3
cd experiments
JOBFILE="../results/logs/jobs_lowdata_v3.txt"
{
  for r in R2 R1 R3; do
    for ((i = 5; i < 20; i++)); do
      echo python3 exp_lowdata.py --phase A --regime "$r" --first $i --count 1 --n-cond 200 --out ../results/lowdata_v3 \
        ">>" "../results/logs/lowA3_${r}_$i.log"
    done
  done
} > "$JOBFILE"
echo "$(wc -l < "$JOBFILE") phase-A jobs, running $JOBS at a time"
xargs -P "$JOBS" -I{} bash -c "{} 2>&1" < "$JOBFILE"
cd ..
python3 scripts/curves_v3.py --dir results/lowdata_v3 --jobs "$JOBS" > results/logs/curves_v3.log 2>&1
echo "all E-low v3 simulation jobs finished"
