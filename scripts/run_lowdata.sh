#!/usr/bin/env bash
# E-low (docs/prereg_lowdata.md): phase A per field (theory CDF, one historical run, oracle), then phase B
# (leave-one-field-out, n_cal = 30) per regime.   JOBS=20 bash scripts/run_lowdata.sh
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS="${JOBS:-$(nproc)}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p results/logs results/lowdata
cd experiments
JOBFILE="../results/logs/jobs_lowdata.txt"
{
  # one job per field (R2 first: largest fields), 200 sampled conditions per field
  for spec in "R2 80 57" "R1 80 60" "R3 80 31"; do
    set -- $spec
    for ((i = 0; i < $3; i++)); do
      echo python3 exp_lowdata.py --phase A --regime "$1" --first $(( $2 + i )) --count 1 --n-cond 200 \
        ">" "../results/logs/lowA_$1_$i.log"
    done
  done
} > "$JOBFILE"
echo "$(wc -l < "$JOBFILE") phase-A jobs, running $JOBS at a time"
xargs -P "$JOBS" -I{} bash -c "{} 2>&1" < "$JOBFILE"
for r in R1 R2 R3; do
  python3 exp_lowdata.py --phase B --regime "$r" --n-cal 30 > "../results/logs/lowB_$r.log" 2>&1 &
done
wait
cp ../results/lowdata/lowdata_R*.csv ../results/ 2>/dev/null || true
echo "all E-low jobs finished"
