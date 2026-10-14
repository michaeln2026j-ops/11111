#!/usr/bin/env bash
# E-low v2 (docs/prereg_lowdata_v2.md): fresh fields 50-79 per regime, fixed theory, ratio pivot.
#   JOBS=4 bash scripts/run_lowdata_v2.sh        (resumable: finished fields are skipped)
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS="${JOBS:-$(nproc)}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
OUTD=../results/lowdata_v2
mkdir -p results/logs results/lowdata_v2
cd experiments
JOBFILE="../results/logs/jobs_lowdata_v2.txt"
{
  for r in R2 R1 R3; do
    for ((i = 50; i < 80; i++)); do
      echo python3 exp_lowdata.py --phase A --regime "$r" --first $i --count 1 --n-cond 200 --out "$OUTD" \
        ">>" "../results/logs/lowA2_${r}_$i.log"
    done
  done
} > "$JOBFILE"
echo "$(wc -l < "$JOBFILE") phase-A jobs, running $JOBS at a time"
xargs -P "$JOBS" -I{} bash -c "{} 2>&1" < "$JOBFILE"
for r in R1 R2 R3; do
  python3 exp_lowdata.py --phase B --regime "$r" --n-cal 29 --out "$OUTD" > "../results/logs/lowB2_$r.log" 2>&1 &
done
wait
echo "all E-low v2 jobs finished"
